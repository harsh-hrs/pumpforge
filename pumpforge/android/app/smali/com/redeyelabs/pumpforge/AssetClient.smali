.class public Lcom/redeyelabs/pumpforge/AssetClient;
.super Landroid/webkit/WebViewClient;
.source "AssetClient.java"

# Serves https://appassets.androidplatform.net/<path> from the APK's assets/<path>.

.field private final assets:Landroid/content/res/AssetManager;


.method public constructor <init>(Landroid/content/res/AssetManager;)V
    .registers 2
    invoke-direct {p0}, Landroid/webkit/WebViewClient;-><init>()V
    iput-object p1, p0, Lcom/redeyelabs/pumpforge/AssetClient;->assets:Landroid/content/res/AssetManager;
    return-void
.end method


.method public shouldInterceptRequest(Landroid/webkit/WebView;Landroid/webkit/WebResourceRequest;)Landroid/webkit/WebResourceResponse;
    .registers 9

    invoke-interface {p2}, Landroid/webkit/WebResourceRequest;->getUrl()Landroid/net/Uri;
    move-result-object v0
    if-eqz v0, :pass

    invoke-virtual {v0}, Landroid/net/Uri;->getHost()Ljava/lang/String;
    move-result-object v1
    const-string v2, "appassets.androidplatform.net"
    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :pass

    invoke-virtual {v0}, Landroid/net/Uri;->getPath()Ljava/lang/String;
    move-result-object v1
    if-eqz v1, :pass
    const/4 v2, 0x1
    invoke-virtual {v1, v2}, Ljava/lang/String;->substring(I)Ljava/lang/String;
    move-result-object v1

    invoke-static {v1}, Lcom/redeyelabs/pumpforge/AssetClient;->mime(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v3

    :try_start
    iget-object v2, p0, Lcom/redeyelabs/pumpforge/AssetClient;->assets:Landroid/content/res/AssetManager;
    invoke-virtual {v2, v1}, Landroid/content/res/AssetManager;->open(Ljava/lang/String;)Ljava/io/InputStream;
    move-result-object v2
    :try_end
    .catch Ljava/io/IOException; {:try_start .. :try_end} :pass

    new-instance v4, Landroid/webkit/WebResourceResponse;
    const-string v5, "UTF-8"
    invoke-direct {v4, v3, v5, v2}, Landroid/webkit/WebResourceResponse;-><init>(Ljava/lang/String;Ljava/lang/String;Ljava/io/InputStream;)V
    return-object v4

    :pass
    const/4 v4, 0x0
    return-object v4
.end method


.method private static mime(Ljava/lang/String;)Ljava/lang/String;
    .registers 3

    const-string v0, ".html"
    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :not_html
    const-string v0, "text/html"
    return-object v0

    :not_html
    const-string v0, ".js"
    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :not_js
    const-string v0, "text/javascript"
    return-object v0

    :not_js
    const-string v0, ".json"
    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :not_json
    const-string v0, "application/json"
    return-object v0

    :not_json
    const-string v0, ".glb"
    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :other
    const-string v0, "model/gltf-binary"
    return-object v0

    :other
    const-string v0, "application/octet-stream"
    return-object v0
.end method
