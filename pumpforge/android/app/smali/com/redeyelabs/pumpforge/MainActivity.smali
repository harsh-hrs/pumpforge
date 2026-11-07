.class public Lcom/redeyelabs/pumpforge/MainActivity;
.super Landroid/app/Activity;
.source "MainActivity.java"

# Full-screen WebView that serves the offline learning library from APK assets
# (https://appassets.androidplatform.net/www/...) and exposes Android TextToSpeech
# to the page as window.AndroidTTS for narrated tours.

.implements Landroid/speech/tts/TextToSpeech$OnInitListener;

.field private tts:Landroid/speech/tts/TextToSpeech;
.field private web:Landroid/webkit/WebView;


.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V
    return-void
.end method


.method protected onCreate(Landroid/os/Bundle;)V
    .registers 6

    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    # WebView with JavaScript + DOM storage
    new-instance v0, Landroid/webkit/WebView;
    invoke-direct {v0, p0}, Landroid/webkit/WebView;-><init>(Landroid/content/Context;)V
    iput-object v0, p0, Lcom/redeyelabs/pumpforge/MainActivity;->web:Landroid/webkit/WebView;

    invoke-virtual {v0}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;
    move-result-object v1
    const/4 v2, 0x1
    invoke-virtual {v1, v2}, Landroid/webkit/WebSettings;->setJavaScriptEnabled(Z)V
    invoke-virtual {v1, v2}, Landroid/webkit/WebSettings;->setDomStorageEnabled(Z)V

    # serve bundled assets
    new-instance v1, Lcom/redeyelabs/pumpforge/AssetClient;
    invoke-virtual {p0}, Landroid/app/Activity;->getAssets()Landroid/content/res/AssetManager;
    move-result-object v2
    invoke-direct {v1, v2}, Lcom/redeyelabs/pumpforge/AssetClient;-><init>(Landroid/content/res/AssetManager;)V
    invoke-virtual {v0, v1}, Landroid/webkit/WebView;->setWebViewClient(Landroid/webkit/WebViewClient;)V

    # text-to-speech bridge for tour narration
    new-instance v1, Landroid/speech/tts/TextToSpeech;
    invoke-direct {v1, p0, p0}, Landroid/speech/tts/TextToSpeech;-><init>(Landroid/content/Context;Landroid/speech/tts/TextToSpeech$OnInitListener;)V
    iput-object v1, p0, Lcom/redeyelabs/pumpforge/MainActivity;->tts:Landroid/speech/tts/TextToSpeech;

    new-instance v2, Lcom/redeyelabs/pumpforge/TtsBridge;
    invoke-direct {v2, v1}, Lcom/redeyelabs/pumpforge/TtsBridge;-><init>(Landroid/speech/tts/TextToSpeech;)V
    const-string v3, "AndroidTTS"
    invoke-virtual {v0, v2, v3}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    invoke-virtual {p0, v0}, Landroid/app/Activity;->setContentView(Landroid/view/View;)V

    const-string v3, "https://appassets.androidplatform.net/www/index.html"
    invoke-virtual {v0, v3}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V
    return-void
.end method


.method public onInit(I)V
    .registers 2
    return-void
.end method


.method protected onDestroy()V
    .registers 2

    iget-object v0, p0, Lcom/redeyelabs/pumpforge/MainActivity;->tts:Landroid/speech/tts/TextToSpeech;
    if-eqz v0, :no_tts
    invoke-virtual {v0}, Landroid/speech/tts/TextToSpeech;->shutdown()V

    :no_tts
    iget-object v0, p0, Lcom/redeyelabs/pumpforge/MainActivity;->web:Landroid/webkit/WebView;
    if-eqz v0, :no_web
    invoke-virtual {v0}, Landroid/webkit/WebView;->destroy()V

    :no_web
    invoke-super {p0}, Landroid/app/Activity;->onDestroy()V
    return-void
.end method
