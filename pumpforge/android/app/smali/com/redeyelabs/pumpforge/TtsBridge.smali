.class public Lcom/redeyelabs/pumpforge/TtsBridge;
.super Ljava/lang/Object;
.source "TtsBridge.java"

# window.AndroidTTS.speak(text) / .stop() for narrated in-app tours.

.field private final tts:Landroid/speech/tts/TextToSpeech;


.method public constructor <init>(Landroid/speech/tts/TextToSpeech;)V
    .registers 2
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/redeyelabs/pumpforge/TtsBridge;->tts:Landroid/speech/tts/TextToSpeech;
    return-void
.end method


.method public speak(Ljava/lang/String;)V
    .registers 6
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/redeyelabs/pumpforge/TtsBridge;->tts:Landroid/speech/tts/TextToSpeech;
    const/4 v1, 0x0
    const/4 v2, 0x0
    const-string v3, "pumpforge"
    invoke-virtual {v0, p1, v1, v2, v3}, Landroid/speech/tts/TextToSpeech;->speak(Ljava/lang/CharSequence;ILandroid/os/Bundle;Ljava/lang/String;)I
    return-void
.end method


.method public stop()V
    .registers 2
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/redeyelabs/pumpforge/TtsBridge;->tts:Landroid/speech/tts/TextToSpeech;
    invoke-virtual {v0}, Landroid/speech/tts/TextToSpeech;->stop()I
    return-void
.end method
