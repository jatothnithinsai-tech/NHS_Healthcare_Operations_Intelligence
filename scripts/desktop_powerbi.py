"""Inspect only this project's Power BI Desktop window; preserve other projects.

Launch uses a new process and records its PID. UI elements are enumerated only
under that process. Screenshots capture its own window, never the full desktop.
"""
from __future__ import annotations
import argparse
import ctypes
import json
import subprocess
import time
import win32gui
import win32process
import win32ui
from PIL import Image
from src.ingestion.acquire import ROOT

STATE=ROOT/'.local/powerbi_desktop.json'


def launch():
    cmd=['powershell','-NoProfile','-Command',"(Get-Process -Name PBIDesktop | Select-Object -First 1).Path"]
    binary=subprocess.check_output(cmd,text=True).strip()
    if not binary:
        raise RuntimeError('Cannot locate installed Power BI Desktop')
    # GUI is explicitly needed for the requested desktop-open test.
    p=subprocess.Popen([binary,str(ROOT/'powerbi/NHS_Healthcare_Operations_Intelligence.pbip')])
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps({'pid':p.pid,'binary':binary,'launched_at':time.time()},indent=2))
    print('Launched this Power BI project; process',p.pid)


def windows():
    state=json.loads(STATE.read_text())
    result=[]
    def callback(hwnd,_):
        _,pid=win32process.GetWindowThreadProcessId(hwnd)
        title=win32gui.GetWindowText(hwnd)
        if pid==state['pid'] and win32gui.IsWindowVisible(hwnd):
            result.append({'hwnd':hwnd,'pid':pid,'title':title})
    win32gui.EnumWindows(callback,None)
    return result


def capture(hwnd,name):
    rect=win32gui.GetWindowRect(hwnd)
    width,height=rect[2]-rect[0],rect[3]-rect[1]
    dc=win32gui.GetWindowDC(hwnd)
    source=win32ui.CreateDCFromHandle(dc)
    target=source.CreateCompatibleDC()
    bitmap=win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(source,width,height)
    target.SelectObject(bitmap)
    ok=ctypes.windll.user32.PrintWindow(hwnd,target.GetSafeHdc(),2)
    info=bitmap.GetInfo()
    im=Image.frombuffer('RGB',(info['bmWidth'],info['bmHeight']),bitmap.GetBitmapBits(True),'raw','BGRX',0,1)
    p=ROOT/'screenshots'/name
    p.parent.mkdir(exist_ok=True)
    im.save(p)
    target.DeleteDC()
    source.DeleteDC()
    win32gui.ReleaseDC(hwnd,dc)
    win32gui.DeleteObject(bitmap.GetHandle())
    print('Captured project window',p.name,'PrintWindow=',ok)


def inspect(capture_name='powerbi_desktop_verification.png'):
    found=windows()
    print(json.dumps(found,indent=2))
    (ROOT/'.local/powerbi_windows.json').write_text(json.dumps(found,indent=2))
    if found:
        main=next((x for x in found if 'NHS_Healthcare' in x['title']),found[-1])
        if win32gui.IsIconic(main['hwnd']):
            win32gui.ShowWindow(main['hwnd'],9)
            time.sleep(1)
        capture(main['hwnd'],capture_name)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['launch','inspect','close'])
    p.add_argument('--capture-name',default='powerbi_desktop_verification.png')
    args=p.parse_args()
    if args.action=='launch':
        launch()
    elif args.action=='close':
        for window in windows():
            if 'NHS_Healthcare' in window['title']:
                win32gui.PostMessage(window['hwnd'],0x0010,0,0)
                print('Requested close of the saved NHS project window only')
    else:
        inspect(args.capture_name)
