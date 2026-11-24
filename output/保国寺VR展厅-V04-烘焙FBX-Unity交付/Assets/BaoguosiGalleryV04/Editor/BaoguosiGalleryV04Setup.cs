#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

// Editor-only, offline, no XR SDK dependency. Only writes under this asset folder.
[InitializeOnLoad]
public static class BaoguosiGalleryV04Setup
{
    public const string Root = "Assets/BaoguosiGalleryV04";
    const string ModelPath = Root + "/Models/Baoguosi_Gallery_V04_Baked.fbx";
    [Serializable] public sealed class Entry { public string name; public string texture; public bool transparent; public bool double_sided; }
    [Serializable] public sealed class Manifest { public Entry[] materials; }
    static bool queued, working;
    static BaoguosiGalleryV04Setup() { Queue(); }
    public static void Queue()
    {
        if (queued || working) return;
        queued = true;
        EditorApplication.delayCall += () => {
            queued = false;
            if (EditorApplication.isCompiling || EditorApplication.isUpdating) { Queue(); return; }
            if (!File.Exists(ModelPath) || !File.Exists(Root + "/MaterialManifest.json")) return;
            try { Configure(false); }
            catch (Exception e) { Debug.LogError("保国寺 V04 材质配置：" + e.Message); }
        };
    }
    static Manifest ReadManifest()
    {
        var m = JsonUtility.FromJson<Manifest>(File.ReadAllText(Root + "/MaterialManifest.json"));
        if (m == null || m.materials == null || m.materials.Length == 0) throw new InvalidOperationException("缺少材质清单，请完整复制 BaoguosiGalleryV04 文件夹。");
        return m;
    }
    static bool IsUrp()
    {
        var pipeline = GraphicsSettings.currentRenderPipeline;
        if (pipeline == null) return false;
        if (pipeline.GetType().Name.IndexOf("Universal", StringComparison.OrdinalIgnoreCase) >= 0) return true;
        throw new InvalidOperationException("本包提供 Built-in 与 URP 方案；工具不会更改项目渲染管线。当前项目请先切换至其中一种。");
    }
    static Shader DisplayShader(bool transparent)
    {
        string name = IsUrp() ? "Universal Render Pipeline/Unlit" : transparent ? "Baoguosi/V04/UnlitTransparentTwoSided" : "Unlit/Texture";
        var shader = Shader.Find(name);
        if (shader == null) throw new InvalidOperationException("未找到显示材质：" + name + "。请确认 Shaders 文件夹也已导入。");
        return shader;
    }
    static void Folder(string path)
    {
        path = path.Replace('\\','/');
        if (AssetDatabase.IsValidFolder(path)) return;
        string parent = Path.GetDirectoryName(path).Replace('\\','/'); Folder(parent);
        AssetDatabase.CreateFolder(parent,Path.GetFileName(path));
    }
    static Texture2D Texture(Entry e)
    {
        string path = Root + "/Textures/" + e.texture;
        var t = AssetImporter.GetAtPath(path) as TextureImporter;
        if (t == null) throw new FileNotFoundException("缺少贴图：" + path);
        bool swatch = e.texture.StartsWith("Swatch_",StringComparison.Ordinal);
        TextureImporterAlphaSource alpha = e.transparent ? TextureImporterAlphaSource.FromInput : TextureImporterAlphaSource.None;
        var compression = swatch ? TextureImporterCompression.Uncompressed : TextureImporterCompression.Compressed;
        bool changed = !t.sRGBTexture || t.mipmapEnabled == swatch || t.maxTextureSize != 2048 || t.alphaSource != alpha || t.wrapMode != TextureWrapMode.Clamp || t.textureCompression != compression;
        t.textureType = TextureImporterType.Default; t.sRGBTexture = true; t.mipmapEnabled = !swatch; t.maxTextureSize = 2048;
        t.alphaSource = alpha; t.alphaIsTransparency = e.transparent; t.wrapMode = TextureWrapMode.Clamp;
        t.filterMode = FilterMode.Trilinear; t.anisoLevel = swatch ? 1 : 4; t.textureCompression = compression;
        var android = t.GetPlatformTextureSettings("Android");
        if (!swatch && (!android.overridden || android.format != TextureImporterFormat.ASTC_6x6 || android.maxTextureSize != 2048))
        { android.overridden = true; android.format = TextureImporterFormat.ASTC_6x6; android.maxTextureSize = 2048; t.SetPlatformTextureSettings(android); changed = true; }
        if (changed) t.SaveAndReimport();
        return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
    }
    static void Set(Material m,string name,float value) { if(m.HasProperty(name)) m.SetFloat(name,value); }
    static Material MaterialFor(Entry e)
    {
        string path = Root + "/Materials/" + e.name + ".mat";
        var mat = AssetDatabase.LoadAssetAtPath<Material>(path); Shader shader = DisplayShader(e.transparent);
        if (mat == null) { mat = new Material(shader); mat.name = e.name; AssetDatabase.CreateAsset(mat,path); }
        mat.shader = shader; var texture = Texture(e);
        foreach (string property in new[]{"_MainTex","_BaseMap"}) if (mat.HasProperty(property)) mat.SetTexture(property,texture);
        foreach (string property in new[]{"_BaseColor","_Color"}) if (mat.HasProperty(property)) mat.SetColor(property,Color.white);
        Set(mat,"_Cull",e.double_sided ? 0 : 2); Set(mat,"_AlphaClip",0); Set(mat,"_Surface",e.transparent ? 1 : 0); Set(mat,"_Blend",0);
        Set(mat,"_ZWrite",e.transparent ? 0 : 1); Set(mat,"_SrcBlend",e.transparent ? (float)BlendMode.SrcAlpha : (float)BlendMode.One);
        Set(mat,"_DstBlend",e.transparent ? (float)BlendMode.OneMinusSrcAlpha : (float)BlendMode.Zero);
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON"); mat.DisableKeyword("_ALPHAMODULATE_ON");
        if (e.transparent) mat.EnableKeyword("_SURFACE_TYPE_TRANSPARENT"); else mat.DisableKeyword("_SURFACE_TYPE_TRANSPARENT");
        mat.SetOverrideTag("RenderType",e.transparent ? "Transparent" : "Opaque"); mat.renderQueue = e.transparent ? 3000 : 2000;
        mat.enableInstancing = true; mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None; EditorUtility.SetDirty(mat); return mat;
    }
    [MenuItem("榫卯智言/展厅V04/1 配置或修复烘焙材质")]
    public static void RepairMaterials() { Configure(true); }
    static void Configure(bool notify)
    {
        if (working) return; working = true;
        try
        {
            Folder(Root + "/Materials"); var manifest = ReadManifest();
            var importer = AssetImporter.GetAtPath(ModelPath) as ModelImporter;
            if (importer == null) throw new InvalidOperationException("FBX 正在导入，请稍后再点击菜单 1。");
            bool changed = importer.importCameras || importer.importLights || importer.importAnimation || importer.generateSecondaryUV || importer.isReadable || importer.materialImportMode != ModelImporterMaterialImportMode.ImportStandard;
            importer.importCameras = false; importer.importLights = false; importer.importAnimation = false; importer.generateSecondaryUV = false; importer.isReadable = false;
            importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
            var map = importer.GetExternalObjectMap();
            foreach (var e in manifest.materials)
            {
                var material = MaterialFor(e); var id = new AssetImporter.SourceAssetIdentifier(typeof(Material),e.name); UnityEngine.Object mapped;
                if (!map.TryGetValue(id,out mapped) || mapped != material) { importer.AddRemap(id,material); changed = true; }
            }
            AssetDatabase.SaveAssets(); if(changed) importer.SaveAndReimport();
            if(notify) EditorUtility.DisplayDialog("保国寺 V04","烘焙贴图及半透明纱幅材质已配置。\n下一步：菜单 2 创建展厅预制体，菜单 3 创建场景。","确定");
        }
        finally { working = false; }
    }
    static GameObject BuildPrefab(bool notify)
    {
        Configure(false); var asset = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
        if(asset == null) throw new InvalidOperationException("请等待模型导入完成。");
        Folder(Root + "/Prefabs"); Scene preview = EditorSceneManager.NewPreviewScene(); GameObject saved;
        try
        {
            var instance = (GameObject)PrefabUtility.InstantiatePrefab(asset,preview); instance.name = "保国寺数字斗拱展厅 V04";
            foreach(var r in instance.GetComponentsInChildren<Renderer>(true))
            {
                r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false; r.lightProbeUsage = LightProbeUsage.Off; r.reflectionProbeUsage = ReflectionProbeUsage.Off;
                if(r.name.StartsWith("BGV04_Architecture_",StringComparison.Ordinal) || r.name.StartsWith("BGV04_Exhibits_",StringComparison.Ordinal))
                {
                    var filter = r.GetComponent<MeshFilter>();
                    if(filter != null && r.GetComponent<MeshCollider>() == null) { var c = r.gameObject.AddComponent<MeshCollider>(); c.sharedMesh = filter.sharedMesh; c.convex = false; }
                }
            }
            saved = PrefabUtility.SaveAsPrefabAsset(instance,Root + "/Prefabs/BaoguosiGalleryV04.prefab");
        }
        finally { EditorSceneManager.ClosePreviewScene(preview); }
        Selection.activeObject = saved;
        if(notify) EditorUtility.DisplayDialog("预制体已生成","已设置静态光影材质，并为建筑和展陈添加静态碰撞体。\n保留 8 个 VR_Teleport_Zone 定位点。未添加摄像机、灯光或 XR SDK。","确定");
        return saved;
    }
    [MenuItem("榫卯智言/展厅V04/2 创建或更新展厅预制体")]
    public static void CreatePrefab() { BuildPrefab(true); }
    [MenuItem("榫卯智言/展厅V04/3 创建展厅场景（无摄像机）")]
    public static void CreateScene()
    {
        var prefab = BuildPrefab(false); Folder(Root + "/Scenes");
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Additive); SceneManager.SetActiveScene(scene);
        var gallery = (GameObject)PrefabUtility.InstantiatePrefab(prefab,scene);
        EditorSceneManager.SaveScene(scene,AssetDatabase.GenerateUniqueAssetPath(Root + "/Scenes/BaoguosiGalleryV04.unity")); Selection.activeGameObject = gallery;
        var anchors = gallery.GetComponentsInChildren<Transform>(true);
        var a = anchors.FirstOrDefault(t=>t.name=="VR_Teleport_Zone05"); var b = anchors.FirstOrDefault(t=>t.name=="VR_Teleport_Zone04");
        if(a != null && b != null && SceneView.lastActiveSceneView != null)
        {
            Vector3 eye = a.position + Vector3.up * 1.7f; Vector3 forward = Vector3.ProjectOnPlane(b.position-a.position,Vector3.up).normalized;
            SceneView.lastActiveSceneView.LookAt(eye+forward*4,Quaternion.LookRotation(forward,Vector3.up),2,false);
        }
        EditorUtility.DisplayDialog("场景已创建","原有场景保持打开，新展厅已另存。\n本场景不包含摄像机、实时灯光或 VR 控制器。\n接入现有 PICO/XR Origin，并为定位点配置瞬移区域即可继续开发。\n请关闭本展厅相机上的额外曝光/色调映射，避免重复处理烘焙颜色。","确定");
    }
    [MenuItem("榫卯智言/展厅V04/4 检查导入资源")]
    public static void Validate()
    {
        var asset = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath); if(asset == null) throw new InvalidOperationException("请先导入 FBX。");
        int bad = 0; var manifest = ReadManifest(); var entries = manifest.materials.ToDictionary(e=>e.name);
        foreach(var r in asset.GetComponentsInChildren<Renderer>(true)) foreach(var m in r.sharedMaterials)
        {
            Entry e; if(m == null || !entries.TryGetValue(m.name,out e)) { bad++; continue; }
            string prop = m.HasProperty("_BaseMap") ? "_BaseMap" : "_MainTex";
            if(m.shader != DisplayShader(e.transparent) || m.GetTexture(prop) == null || (e.transparent && m.renderQueue < 3000)) bad++;
        }
        int cameras = asset.GetComponentsInChildren<Camera>(true).Length; int lights = asset.GetComponentsInChildren<Light>(true).Length;
        int anchors = asset.GetComponentsInChildren<Transform>(true).Count(t=>t.name.StartsWith("VR_Teleport_Zone",StringComparison.Ordinal));
        string message = "异常材质/贴图："+bad+"\n摄像机："+cameras+"\n实时灯光："+lights+"\nVR 定位点："+anchors+"\n渲染网格："+asset.GetComponentsInChildren<Renderer>(true).Length;
        bool ok = bad==0 && cameras==0 && lights==0 && anchors==8; Debug.Log("保国寺 V04 导入检查\n"+message);
        EditorUtility.DisplayDialog(ok ? "导入检查通过" : "请检查资源",message+"\n此检查不代替 PICO 头盔实机测试。","确定");
    }
}
public sealed class BaoguosiGalleryV04AssetWatcher : AssetPostprocessor
{
    static void OnPostprocessAllAssets(string[] imported,string[] deleted,string[] moved,string[] movedFrom)
    {
        if(imported.Any(p=>p.StartsWith(BaoguosiGalleryV04Setup.Root+"/Models/",StringComparison.Ordinal) || p.StartsWith(BaoguosiGalleryV04Setup.Root+"/Textures/",StringComparison.Ordinal) || p==BaoguosiGalleryV04Setup.Root+"/MaterialManifest.json")) BaoguosiGalleryV04Setup.Queue();
    }
}
#endif
