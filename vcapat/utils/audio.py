"""Procedurally generate a short, royalty-free lock/loss sound; no playback side effects."""
import io,math,struct,wave

def cue_wav(event='lock',duration_s=.17,rate=22050):
    if event not in ('lock','loss'):raise ValueError('event must be lock or loss')
    pitch=880 if event=='lock' else 330
    result=io.BytesIO()
    with wave.open(result,'wb') as output:
        output.setnchannels(1);output.setsampwidth(2);output.setframerate(rate)
        for i in range(int(duration_s*rate)):
            t=i/rate;envelope=min(1,t/.015)*max(0,1-t/duration_s)
            sample=int(8500*math.sin(2*math.pi*pitch*t)*envelope)
            output.writeframesraw(struct.pack('<h',sample))
    return result.getvalue()
