import asyncio,os,subprocess,sys,time,threading,http.server,functools
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).parent
async def main():
 frames=ROOT/'frames';frames.mkdir(exist_ok=True)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',8765),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--hide-scrollbars'])
  page=await browser.new_page(viewport={'width':1440,'height':810},device_scale_factor=1)
  await page.goto('http://127.0.0.1:8765/index.html');await page.wait_for_load_state('load');await page.evaluate('document.fonts.ready')
  fps=int(os.environ.get('FPS','20'));duration=float(os.environ.get('DURATION','26'));count=int(fps*duration)
  start=time.time()
  for i in range(count):
   await page.evaluate('(t)=>window.setDemoTime(t)',i/fps)
   await page.screenshot(path=str(frames/f'{i:05}.jpg'),type='jpeg',quality=83,animations='disabled')
   if i%80==0:print(f'captured {i}/{count}, elapsed {time.time()-start:.1f}s',flush=True)
  await browser.close()
 cmd=['ffmpeg','-y','-loglevel','error','-framerate',str(fps),'-i',str(frames/'%05d.jpg'),'-vf','scale=1920:1080:flags=lanczos,format=yuv420p','-c:v','libx264','-preset','medium','-crf','19','-movflags','+faststart',str(ROOT/'medgarant-homepage-animation.mp4')]
 subprocess.run(cmd,check=True);print('DONE video',ROOT/'medgarant-homepage-animation.mp4')
asyncio.run(main())
