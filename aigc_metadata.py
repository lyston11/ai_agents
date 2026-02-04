"""
AIGC 图片元数据检测工具
支持检测: 
- C2PA 认证 (Google/Adobe/Microsoft 等国际标准)
- 中国 AIGC 国家标准 (XMP AIGC 字段)
- Stable Diffusion, ComfyUI, NovelAI
- 通用 XMP/EXIF 元数据
"""

from PIL import Image
from PIL.ExifTags import TAGS
import json
import struct
import sys
import re
from pathlib import Path

# 尝试导入 c2pa 库
try:
    import c2pa
    C2PA_AVAILABLE = True
except ImportError:
    C2PA_AVAILABLE = False


def read_c2pa_metadata(filepath):
    """使用 c2pa 库读取完整的 C2PA 元数据"""
    if not C2PA_AVAILABLE:
        return None
    
    try:
        path = Path(filepath)
        with c2pa.Reader(path) as reader:
            manifest_json = reader.json()
            return json.loads(manifest_json)
    except Exception as e:
        return None


def parse_c2pa_info(c2pa_data):
    """从 C2PA 数据中提取关键信息"""
    if not c2pa_data:
        return None
    
    info = {
        "验证状态": c2pa_data.get("validation_state", "未知"),
        "活动清单": c2pa_data.get("active_manifest", ""),
    }
    
    # 获取活动清单的详细信息
    active_manifest_id = c2pa_data.get("active_manifest")
    manifests = c2pa_data.get("manifests", {})
    
    if active_manifest_id and active_manifest_id in manifests:
        manifest = manifests[active_manifest_id]
        
        # 签名信息
        sig_info = manifest.get("signature_info", {})
        if sig_info:
            info["签名者"] = sig_info.get("issuer", "未知")
            info["签名服务"] = sig_info.get("common_name", "")
            info["签名时间"] = sig_info.get("time", "")
            info["签名算法"] = sig_info.get("alg", "")
        
        # 生成器信息
        gen_info = manifest.get("claim_generator_info", [])
        if gen_info:
            info["生成器"] = gen_info[0].get("name", "未知")
            info["生成器版本"] = gen_info[0].get("version", "")
        
        # 操作历史
        assertions = manifest.get("assertions", [])
        actions = []
        for assertion in assertions:
            if assertion.get("label") == "c2pa.actions.v2":
                action_data = assertion.get("data", {}).get("actions", [])
                for action in action_data:
                    action_info = {
                        "操作": action.get("action", ""),
                        "描述": action.get("description", ""),
                        "来源类型": action.get("digitalSourceType", "")
                    }
                    actions.append(action_info)
        
        if actions:
            info["操作历史"] = actions
    
    return info


def extract_xmp(filepath):
    """从图片文件中提取 XMP 元数据"""
    xmp_data = None
    
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # 查找 XMP 数据块
        xmp_start_markers = [b'<?xpacket', b'<x:xmpmeta', b'<rdf:RDF']
        xmp_end_markers = [b'<?xpacket end', b'</x:xmpmeta>', b'</rdf:RDF>']
        
        for start_marker, end_marker in zip(xmp_start_markers, xmp_end_markers):
            start_idx = content.find(start_marker)
            if start_idx != -1:
                end_idx = content.find(end_marker, start_idx)
                if end_idx != -1:
                    xmp_data = content[start_idx:end_idx + len(end_marker) + 20]
                    try:
                        xmp_data = xmp_data.decode('utf-8', errors='ignore')
                    except:
                        pass
                    break
    except Exception as e:
        pass
    
    return xmp_data


def parse_aigc_from_xmp(xmp_string):
    """从 XMP 字符串中解析 AIGC 字段（中国国家标准）"""
    aigc_info = {}
    
    if not xmp_string:
        return aigc_info
    
    # 方法1: 直接用正则匹配 AIGC 相关字段
    aigc_pattern = r'"AIGC"\s*:\s*(\{[^}]+\})'
    match = re.search(aigc_pattern, xmp_string)
    if match:
        try:
            aigc_info = json.loads(match.group(1))
            return {"AIGC": aigc_info}
        except:
            pass
    
    # 方法2: 匹配 XML 格式的 AIGC 标签
    patterns = {
        'Label': r'<[^>]*:?Label[^>]*>([^<]+)<',
        'ContentProducer': r'<[^>]*:?ContentProducer[^>]*>([^<]+)<',
        'ProduceID': r'<[^>]*:?ProduceID[^>]*>([^<]+)<',
        'Propagator': r'<[^>]*:?Propagator[^>]*>([^<]+)<',
        'PropatorID': r'<[^>]*:?PropatorID[^>]*>([^<]+)<',
        'ReserveCode1': r'<[^>]*:?ReserveCode1[^>]*>([^<]+)<',
        'ReserveCode2': r'<[^>]*:?ReserveCode2[^>]*>([^<]+)<',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, xmp_string, re.IGNORECASE)
        if match:
            aigc_info[key] = match.group(1)
    
    # 方法3: 检查是否包含 AIGC 相关关键词
    if not aigc_info:
        if 'AIGC' in xmp_string or 'aigc' in xmp_string:
            aigc_info['raw_aigc_detected'] = True
            if 'ContentProducer' in xmp_string:
                cp_match = re.search(r'ContentProducer["\s:]+([^",}\s]+)', xmp_string)
                if cp_match:
                    aigc_info['ContentProducer'] = cp_match.group(1)
    
    return {"AIGC": aigc_info} if aigc_info else {}


def read_png_chunks(filepath):
    """读取 PNG 文件的所有 chunks"""
    chunks = {}
    try:
        with open(filepath, 'rb') as f:
            # 跳过 PNG 签名 (8 bytes)
            f.read(8)
            
            while True:
                try:
                    length_data = f.read(4)
                    if len(length_data) < 4:
                        break
                    length = struct.unpack('>I', length_data)[0]
                    chunk_type = f.read(4).decode('ascii', errors='ignore')
                    
                    data = f.read(length)
                    f.read(4)  # CRC
                    
                    if chunk_type in ['tEXt', 'iTXt', 'zTXt']:
                        try:
                            if chunk_type == 'tEXt':
                                null_idx = data.index(b'\x00')
                                key = data[:null_idx].decode('latin-1')
                                value = data[null_idx+1:].decode('latin-1', errors='replace')
                                chunks[key] = value
                            elif chunk_type == 'iTXt':
                                parts = data.split(b'\x00', 4)
                                if len(parts) >= 5:
                                    key = parts[0].decode('utf-8', errors='replace')
                                    value = parts[4].decode('utf-8', errors='replace')
                                    chunks[key] = value
                        except:
                            pass
                            
                    if chunk_type == 'IEND':
                        break
                except:
                    break
    except:
        pass
    return chunks


def detect_aigc_source(filepath):
    """检测 AIGC 图片的来源和元数据"""
    results = {
        "source": "未知",
        "metadata": {},
        "basic_info": {},
        "aigc_standard": None,  # 中国 AIGC 国家标准信息
        "c2pa": None,  # C2PA 认证信息
        "c2pa_raw": None  # C2PA 原始数据
    }
    
    try:
        img = Image.open(filepath)
        
        # 基本信息
        results["basic_info"] = {
            "格式": img.format,
            "尺寸": f"{img.size[0]} x {img.size[1]}",
            "模式": img.mode
        }
        
        # ========== 优先检查: C2PA 认证 (国际标准) ==========
        c2pa_raw = read_c2pa_metadata(filepath)
        if c2pa_raw:
            results["c2pa_raw"] = c2pa_raw
            results["c2pa"] = parse_c2pa_info(c2pa_raw)
            
            # 根据 C2PA 内容确定来源
            if results["c2pa"]:
                generator = results["c2pa"].get("生成器", "")
                issuer = results["c2pa"].get("签名者", "")
                
                if "Google" in generator or "Google" in issuer:
                    results["source"] = "Google AI (Gemini/Imagen)"
                elif "Adobe" in generator or "Adobe" in issuer:
                    results["source"] = "Adobe 产品"
                elif "Microsoft" in generator or "Microsoft" in issuer:
                    results["source"] = "Microsoft AI"
                else:
                    results["source"] = f"C2PA 认证 ({issuer})"
        
        # ========== 检查: 中国 AIGC 国家标准 (XMP) ==========
        if results["source"] == "未知":
            xmp_data = extract_xmp(filepath)
            if xmp_data:
                aigc_info = parse_aigc_from_xmp(xmp_data)
                if aigc_info and aigc_info.get("AIGC"):
                    results["aigc_standard"] = aigc_info["AIGC"]
                    results["source"] = "符合中国 AIGC 国家标准"
        
        # ========== 检查 PNG 元数据 (Stable Diffusion, ComfyUI, NovelAI 等) ==========
        if img.format == 'PNG':
            for key, value in img.info.items():
                if isinstance(value, (str, bytes)):
                    results["metadata"][key] = value if isinstance(value, str) else value.decode('utf-8', errors='replace')
            
            png_chunks = read_png_chunks(filepath)
            results["metadata"].update(png_chunks)
            
            # 检查 PNG 元数据中的 AIGC 字段 (中国国家标准)
            if "AIGC" in results["metadata"] and results["source"] == "未知":
                try:
                    aigc_str = results["metadata"]["AIGC"]
                    aigc_data = json.loads(aigc_str)
                    results["aigc_standard"] = aigc_data
                    
                    # 根据 ContentProducer 确定来源
                    producer = aigc_data.get("ContentProducer", "").lower()
                    if producer == "doubao":
                        results["source"] = "豆包 AI (字节跳动)"
                    elif producer == "wenxin" or "baidu" in producer:
                        results["source"] = "百度文心一格"
                    elif producer == "tongyi" or "aliyun" in producer or "alibaba" in producer:
                        results["source"] = "阿里通义万相"
                    elif producer == "midjourney":
                        results["source"] = "Midjourney"
                    elif producer:
                        results["source"] = f"AIGC ({producer})"
                    else:
                        results["source"] = "符合中国 AIGC 国家标准"
                except:
                    pass
            
            if results["source"] == "未知":
                if "parameters" in results["metadata"]:
                    results["source"] = "Stable Diffusion (A1111/Forge)"
                elif "prompt" in results["metadata"]:
                    if "workflow" in results["metadata"]:
                        results["source"] = "ComfyUI"
                    else:
                        results["source"] = "Stable Diffusion 变体"
                elif "Comment" in results["metadata"]:
                    comment = results["metadata"]["Comment"]
                    if "novelai" in comment.lower() or "nai" in comment.lower():
                        results["source"] = "NovelAI"
                    else:
                        results["source"] = "带 Comment 的 PNG"
                elif "Software" in results["metadata"]:
                    results["source"] = f"软件: {results['metadata']['Software']}"
        
        # ========== 检查 EXIF (JPEG 等) ==========
        if hasattr(img, '_getexif') and img._getexif():
            exif = img._getexif()
            for tag_id, value in exif.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if isinstance(value, bytes):
                    try:
                        value = value.decode('utf-8', errors='replace')
                    except:
                        value = str(value)
                results["metadata"][str(tag_name)] = value
            
            if "UserComment" in results["metadata"] and results["source"] == "未知":
                results["source"] = "带 EXIF UserComment 的图片"
        
    except Exception as e:
        results["error"] = str(e)
    
    return results


def print_results(results):
    """美化输出结果"""
    print("\n" + "=" * 70)
    print("🔍 AIGC 图片元数据检测结果")
    print("=" * 70)
    
    print(f"\n📌 检测到的来源: {results['source']}")
    
    print("\n📊 基本信息:")
    for key, value in results.get("basic_info", {}).items():
        print(f"   {key}: {value}")
    
    # ========== C2PA 认证信息 (国际标准) ==========
    if results.get("c2pa"):
        print("\n" + "-" * 70)
        print("🌍 C2PA 内容认证 (国际标准):")
        print("-" * 70)
        c2pa_info = results["c2pa"]
        
        # 基本信息
        simple_fields = ["验证状态", "签名者", "签名服务", "签名时间", "生成器"]
        for field in simple_fields:
            if field in c2pa_info and c2pa_info[field]:
                print(f"   {field}: {c2pa_info[field]}")
        
        # 操作历史
        if "操作历史" in c2pa_info:
            print("\n   📜 操作历史:")
            for i, action in enumerate(c2pa_info["操作历史"], 1):
                action_type = action.get("操作", "").replace("c2pa.", "")
                desc = action.get("描述", "")
                source_type = action.get("来源类型", "")
                
                print(f"      {i}. {action_type}")
                if desc:
                    print(f"         描述: {desc}")
                if source_type:
                    # 简化来源类型显示
                    source_simple = source_type.split("/")[-1] if "/" in source_type else source_type
                    print(f"         来源类型: {source_simple}")
        
        print("-" * 70)
    
    # ========== 中国 AIGC 国家标准信息 ==========
    if results.get("aigc_standard"):
        print("\n" + "-" * 70)
        print("🇨🇳 中国 AIGC 国家标准元数据:")
        print("-" * 70)
        aigc = results["aigc_standard"]
        
        field_names = {
            "Label": "标签 (1=AI生成)",
            "ContentProducer": "内容生产者",
            "ProduceID": "产品ID",
            "Propagator": "传播者",
            "PropatorID": "传播者ID",
            "ContentPropagator": "内容传播者",
            "PropagateID": "传播ID",
            "ReserveCode1": "保留码1",
            "ReserveCode2": "保留码2",
            "ReservedCode1": "保留码1",
            "ReservedCode2": "保留码2",
            "raw_aigc_detected": "AIGC标记"
        }
        
        for key, value in aigc.items():
            display_name = field_names.get(key, key)
            print(f"   {display_name}: {value}")
        print("-" * 70)
    
    # ========== 其他元数据 ==========
    # 过滤掉已经在 C2PA 中显示的信息
    other_metadata = {k: v for k, v in results.get("metadata", {}).items() 
                      if k not in ["C2PA", "XMP"]}
    
    if other_metadata:
        print("\n📝 其他元数据:")
        for key, value in other_metadata.items():
            if isinstance(value, str) and len(value) > 200:
                display_value = value[:200] + "... [已截断]"
            else:
                display_value = value
            print(f"   {key}: {display_value}")
    
    # ========== 无元数据提示 ==========
    if not results.get("metadata") and not results.get("aigc_standard") and not results.get("c2pa"):
        print("\n❌ 未找到 AIGC 元数据")
        print("   提示: 以下情况可能没有元数据:")
        print("   - Midjourney (不嵌入元数据)")
        print("   - DALL-E (不嵌入元数据)")
        print("   - 经过压缩/转换的图片")
        print("   - 截图或重新保存的图片")
    
    if results.get("error"):
        print(f"\n⚠️ 错误: {results['error']}")
    
    # C2PA 库状态
    if not C2PA_AVAILABLE:
        print("\n💡 提示: 安装 c2pa-python 可获取更详细的 C2PA 信息")
        print("   pip install c2pa-python")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=" * 50)
        print("🔍 AIGC 图片元数据检测工具")
        print("=" * 50)
        print("\n使用方法: python aigc_metadata.py <图片路径>")
        print("\n示例:")
        print("  python aigc_metadata.py image.png")
        print("  python aigc_metadata.py ~/Downloads/ai_image.jpg")
        print("\n支持检测:")
        print("  ✅ C2PA 认证 (Google Gemini, Adobe, Microsoft)")
        print("  ✅ 中国 AIGC 国家标准")
        print("  ✅ Stable Diffusion / ComfyUI / NovelAI")
        print("  ✅ 通用 EXIF/XMP 元数据")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # 检查文件是否存在
    if not Path(image_path).exists():
        print(f"❌ 错误: 文件不存在 - {image_path}")
        sys.exit(1)
    
    results = detect_aigc_source(image_path)
    print_results(results)
    
    # 添加 --json 参数支持
    if len(sys.argv) > 2 and sys.argv[2] == "--json":
        print("\n完整 JSON 数据:")
        # 移除原始 C2PA 数据以减少输出
        output = {k: v for k, v in results.items() if k != "c2pa_raw"}
        print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
