# -*- coding: utf-8 -*-

# --------------------------------------------------------------------
# 模块导入 (Imports from both 3.py and main_app.py)
# --------------------------------------------------------------------
import tkinter as tk
from tkinter import messagebox, filedialog, Scale, Checkbutton, BooleanVar, Frame, Label, Entry, Button, Scrollbar, \
    Canvas, Text
import os
import json
import re
import sys
import time

# --------------------------------------------------------------------
# 依赖项检查 (Dependency Checks)
# --------------------------------------------------------------------
try:
    import webview
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("缺少模块", "请先安装 pywebview 模块 (pip install pywebview)")
    sys.exit(1)

try:
    import pygame
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("缺少模块", "请先安装 pygame 模块 (pip install pygame)")
    sys.exit(1)

# --------------------------------------------------------------------
# 内嵌的 HTML 内容 (Embedded HTML Content from 1.html)
# --------------------------------------------------------------------
# 将 1.html 的代码直接作为字符串变量嵌入，这样就无需外部文件
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>生日快乐</title>
<style>
    body{margin:0;padding:0;overflow:hidden;background:#000;height:100%}
    canvas{position:absolute;width:100%;height:100%}
    .text-canvas{position:absolute;width:100%;height:100%;z-index:9999;pointer-events:none}
    .heart-text{position:fixed;top:35%;left:50%;transform:translateX(-50%);z-index:100;pointer-events:none;display:none}
    .heart-text h4{font-family:"STKaiti";font-size:40px;color:#f584b7;text-align:center;white-space:nowrap}
</style>
</head>
<body>
<canvas id="rain-canvas"></canvas>
<canvas class="text-canvas"></canvas>
<div class="heart-text"><h4>&#128151;我会永远<br>陪着你</h4></div>
<canvas id="heart-canvas" style="display:none;"></canvas>
<script>
function initRainEffect(){var e=document.getElementById("rain-canvas"),t=e.getContext("2d");e.height=window.innerHeight,e.width=window.innerWidth;for(var n="I LOVE U".split(""),i=16,o=e.width/i,a=[],r=0;r<o;r++)a[r]=1;function d(){t.fillStyle="rgba(0, 0, 0, 0.05)",t.fillRect(0,0,e.width,e.height),t.fillStyle="#f584b7",t.font=i+"px arial";for(var r=0;r<a.length;r++){var s=n[Math.floor(Math.random()*n.length)];t.fillText(s,r*i,a[r]*i),(a[r]*i>e.height||Math.random()>.95)&&(a[r]=0),a[r]++}}setInterval(d,33),window.addEventListener("resize",function(){e.width=window.innerWidth,e.height=window.innerHeight,o=e.width/i,a=[];for(var t=0;t<o;t++)a[t]=1})}
function initHeartEffect(){var e={particles:{length:500,duration:2,velocity:100,effect:-.75,size:30}},t=function(e,t){this.x=void 0!==e?e:0,this.y=void 0!==t?t:0};t.prototype={clone:function(){return new t(this.x,this.y)},length:function(e){return void 0===e?Math.sqrt(this.x*this.x+this.y*this.y):(this.normalize(),this.x*=e,this.y*=e,this)},normalize:function(){var e=this.length();return this.x/=e,this.y/=e,this}};var n=function(){this.position=new t,this.velocity=new t,this.acceleration=new t,this.age=0};n.prototype={initialize:function(t,i,o,a){this.position.x=t,this.position.y=i,this.velocity.x=o,this.velocity.y=a,this.acceleration.x=o*e.particles.effect,this.acceleration.y=a*e.particles.effect,this.age=0},update:function(e){this.position.x+=this.velocity.x*e,this.position.y+=this.velocity.y*e,this.velocity.x+=this.acceleration.x*e,this.velocity.y+=this.acceleration.y*e,this.age+=e},draw:function(t,n){var i=n.width*function(e){return--e*e*e+1}(this.age/e.particles.duration);t.globalAlpha=1-this.age/e.particles.duration,t.drawImage(n,this.position.x-i/2,this.position.y-i/2,i,i)}};var i=function(t){for(var i=new Array(t),o=0;o<i.length;o++)i[o]=new n;var a=0,r=0,d=e.particles.duration;return{add:function(e,t,n,o){i[r].initialize(e,t,n,o),++r===i.length&&(r=0),a===r&&++a===i.length&&(a=0)},update:function(e){var t;if(a<r)for(t=a;t<r;t++)i[t].update(e);if(r<a){for(t=a;t<i.length;t++)i[t].update(e);for(t=0;t<r;t++)i[t].update(e)}for(;++a===i.length&&(a=0),i[a].age>=d&&a!==r;);},draw:function(e,t){var n;if(a<r)for(n=a;n<r;n++)i[n].draw(e,t);if(r<a){for(n=a;n<i.length;n++)i[n].draw(e,t);for(n=0;n<r;n++)i[n].draw(e,t)}}}};function o(){var n=document.getElementById("heart-canvas"),o=n.getContext("2d");n.style.display="block",n.width=n.clientWidth,n.height=n.clientHeight,document.querySelector(".heart-text").style.display="block";var a=new i(e.particles.length),r=e.particles.length/e.particles.duration,d=function(e){return new t(160*Math.pow(Math.sin(e),3),130*Math.cos(e)-50*Math.cos(2*e)-20*Math.cos(3*e)-10*Math.cos(4*e)+25)}(),s=function(){var n=document.createElement("canvas"),i=n.getContext("2d");n.width=e.particles.size,n.height=e.particles.size;var o=function(t){var n=d(t);return n.x=e.particles.size/2+n.x*e.particles.size/350,n.y=e.particles.size/2-n.y*e.particles.size/350,n};i.beginPath();for(var a=-Math.PI,r=o(a);a<Math.PI;)a+=.01,r=o(a),i.lineTo(r.x,r.y);i.closePath(),i.fillStyle="#ea80b0",i.fill();var s=new Image;return s.src=n.toDataURL(),s}();!function t(){requestAnimationFrame(t);var n,i=(new Date).getTime()/1e3,l=i-(n||i);n=i,o.clearRect(0,0,n.width,n.height);for(var c=r*l,h=0;h<c;h++){var u=d(Math.PI-2*Math.PI*Math.random()),v=u.clone().length(e.particles.velocity);a.add(n.width/2+u.x,n.height/2-u.y,v.x,-v.y)}a.update(l),a.draw(o,s)}(),window.addEventListener("resize",function(){n.width=n.clientWidth,n.height=n.clientHeight})}return{start:o}}
function initTextEffect(){var e={canvas:null,context:null,renderFn:null,requestFrame:window.requestAnimationFrame||window.webkitRequestAnimationFrame||window.mozRequestAnimationFrame||window.oRequestAnimationFrame||window.msRequestAnimationFrame||function(e){window.setTimeout(e,1e3/60)},init:function(t){this.canvas=document.querySelector(t),this.context=this.canvas.getContext("2d"),this.adjustCanvas(),window.addEventListener("resize",function(e){this.adjustCanvas()}.bind(this))},loop:function(t){this.renderFn=this.renderFn?this.renderFn:t,this.clearFrame(),this.renderFn(),this.requestFrame.call(window,this.loop.bind(this))},adjustCanvas:function(){this.canvas.width=window.innerWidth,this.canvas.height=window.innerHeight},clearFrame:function(){this.context.clearRect(0,0,this.canvas.width,this.canvas.height)},getArea:function(){return{w:this.canvas.width,h:this.canvas.height}},drawCircle:function(e,t){this.context.fillStyle=t.render(),this.context.beginPath(),this.context.arc(e.x,e.y,e.z,0,2*Math.PI,!0),this.context.closePath(),this.context.fill()}},t=function(e){this.x=e.x,this.y=e.y,this.z=e.z,this.a=e.a,this.h=e.h},n=function(e,t,n,i){this.r=e,this.g=t,this.b=n,this.a=i,this.render=function(){return"rgba("+this.r+","+this.g+","+this.b+","+this.a+")"}},i=function(i,o){this.p=new t({x:i,y:o,z:5,a:1,h:0}),this.e=.07,this.s=!0,this.c=new n(255,255,255,this.p.a),this.t=this.clone(),this.q=[]};i.prototype={clone:function(){return new t({x:this.x,y:this.y,z:this.z,a:this.a,h:this.h})},_draw:function(){this.c.a=this.p.a,e.drawCircle(this.p,this.c)},_moveTowards:function(e){var t=this.distanceTo(e,!0),n=t[0],i=t[1],o=t[2],a=this.e*o;return-1===this.p.h?(this.p.x=e.x,this.p.y=e.y,!0):o>1?(this.p.x-=n/o*a,this.p.y-=i/o*a,!1):this.p.h>0?(this.p.h--,!1):!0},_update:function(){if(this._moveTowards(this.t)){var e=this.q.shift();e?(this.t.x=e.x||this.p.x,this.t.y=e.y||this.p.y,this.t.z=e.z||this.p.z,this.t.a=e.a||this.p.a,this.p.h=e.h||0):this.s?(this.p.x-=Math.sin(3.142*Math.random()),this.p.y-=Math.sin(3.142*Math.random())):this.move(new t({x:this.p.x+50*Math.random()-25,y:this.p.y+50*Math.random()-25}))}var n=this.p.a-this.t.a;this.p.a=Math.max(.1,this.p.a-.05*n),n=this.p.z-this.t.z,this.p.z=Math.max(1,this.p.z-.05*n)},distanceTo:function(e,t){var n=this.p.x-e.x,i=this.p.y-e.y,o=Math.sqrt(n*n+i*i);return t?[n,i,o]:o},move:function(e,t){t&&this.distanceTo(e)>1||this.q.push(e)},render:function(){this._update(),this._draw()}};var o={dots:[],width:0,height:0,cx:0,cy:0,compensate:function(){var t=e.getArea();this.cx=t.w/2-this.width/2,this.cy=t.h/2-this.height/2},shuffleIdle:function(){for(var t=e.getArea(),n=0;n<this.dots.length;n++)this.dots[n].s||this.dots[n].move({x:Math.random()*t.w,y:Math.random()*t.h})},switchShape:function(n,a){var r,d=e.getArea();if(this.width=n.w,this.height=n.h,this.compensate(),n.dots.length>this.dots.length){r=n.dots.length-this.dots.length;for(var s=1;s<=r;s++)this.dots.push(new i(d.w/2,d.h/2))}for(var l,c=0;n.dots.length>0;)l=Math.floor(Math.random()*n.dots.length),this.dots[c].e=a?.25:this.dots[c].s?.14:.11,this.dots[c].s?this.dots[c].move(new t({z:20*Math.random()+10,a:Math.random(),h:18})):this.dots[c].move(new t({z:5*Math.random()+5,h:a?18:30})),this.dots[c].s=!0,this.dots[c].move(new t({x:n.dots[l].x+this.cx,y:n.dots[l].y+this.cy,a:1,z:5,h:0})),n.dots=n.dots.slice(0,l).concat(n.dots.slice(l+1)),c++;for(s=c;s<this.dots.length;s++)this.dots[s].s&&(this.dots[s].move(new t({z:20*Math.random()+10,a:Math.random(),h:20})),this.dots[s].s=!1,this.dots[s].e=.04,this.dots[s].move(new t({x:Math.random()*d.w,y:Math.random()*d.h,a:.3,z:4*Math.random(),h:0})))},render:function(){for(var e=0;e<this.dots.length;e++)this.dots[e].render()}},a={gap:13,shapeCanvas:document.createElement("canvas"),shapeContext:null,fontSize:500,fontFamily:"Avenir, Helvetica Neue, Helvetica, Arial, sans-serif",init:function(){this.shapeContext=this.shapeCanvas.getContext("2d"),this.fit()},fit:function(){this.shapeCanvas.width=Math.floor(window.innerWidth/this.gap)*this.gap,this.shapeCanvas.height=Math.floor(window.innerHeight/this.gap)*this.gap,this.shapeContext.fillStyle="red",this.shapeContext.textBaseline="middle",this.shapeContext.textAlign="center"},processCanvas:function(){for(var e,n=this.shapeContext.getImageData(0,0,this.shapeCanvas.width,this.shapeCanvas.height).data,i=[],o=0,a=0,r=this.shapeCanvas.width,d=this.shapeCanvas.height,s=0,l=0,c=0;c<n.length;c+=4*this.gap)n[c+3]>0&&(i.push(new t({x:o,y:a})),s=o>s?o:s,l=a>l?a:l,r=o<r?o:r,d=a<d?a:d),o+=this.gap,o>=this.shapeCanvas.width&&(o=0,a+=this.gap,c+=this.gap*4*this.shapeCanvas.width);return{dots:i,w:s+r,h:l+d}},setFontSize:function(e){this.shapeContext.font="bold "+e+"px "+this.fontFamily},letter:function(e){var t=0;return this.fit(),this.setFontSize(this.fontSize),t=Math.min(this.fontSize,.8*(this.shapeCanvas.width/this.shapeContext.measureText(e).width)*this.fontSize,this.shapeCanvas.height/this.fontSize*(isFinite(e)?1:.45)*this.fontSize),this.setFontSize(t),this.shapeContext.clearRect(0,0,this.shapeCanvas.width,this.shapeCanvas.height),this.shapeContext.fillText(e,this.shapeCanvas.width/2,this.shapeCanvas.height/2),this.processCanvas()}};e.init(".text-canvas"),a.init(),e.loop(function(){o.render()}),simulate(["#countdown 3",...["亲爱的","节日快乐","我爱你"],"#rectangle"])}
function simulate(e){var t,n=0;!function i(){if(n<e.length){if(t=e[n],n++,"#countdown 3"===t){var a=3;var r=setInterval(function(){a>0?Shape.switchShape(ShapeBuilder.letter(a),!0):-1<a||(clearInterval(r),i()),a--},1e3)}else"#rectangle"===t?setTimeout(function(){document.querySelector(".text-canvas").style.display="none";var e=initHeartEffect();e.start()},1e3):(Shape.switchShape(ShapeBuilder.letter(t)),setTimeout(i,2e3))}}()}
window.onload=function(){initRainEffect(),initTextEffect()};
</script>
<script>
    document.addEventListener('keydown', function(e) {
        if (e.keyCode === 27) { // ESC key
            if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.close_window === 'function') {
                window.pywebview.api.close_window();
            }
        }
    });
</script>
</body>
</html>
"""


# --------------------------------------------------------------------
# pywebview API 类 (Api class from main_app.py)
# --------------------------------------------------------------------
class Api:
    """提供给 WebView 的 JS API，用于关闭窗口等操作"""

    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def close_window(self):
        if self._window:
            self._window.destroy()


# --------------------------------------------------------------------
# 主程序逻辑 (Main app logic from main_app.py)
# --------------------------------------------------------------------
def show_confession(html_content):
    """
    显示主表白窗口的函数
    :param html_content: 从配置生成的、最终要显示的 HTML 内容
    """
    # 确定 application_path，以便在打包后也能正确找到 config.json 和音乐文件
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    config_file = os.path.join(application_path, 'config.json')

    if not os.path.exists(config_file):
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("错误", "配置文件 'config.json' 未找到！")
        return

    with open(config_file, 'r', encoding='utf-8') as f:
        full_config = json.load(f)

    # 加载配置
    popups_config = full_config.get("popups", [])
    delay = full_config.get("delay", 0)
    music_file_raw = full_config.get("music_file", "")

    # 正确解析音乐文件路径（绝对路径或相对路径）
    if music_file_raw and not os.path.isabs(music_file_raw):
        music_file = os.path.join(application_path, music_file_raw)
    else:
        music_file = music_file_raw

    volume = full_config.get("volume", 0.5)
    final_rejection_text = full_config.get("final_rejection_text", "好吧，看来你真的不喜欢我...")

    if delay > 0:
        time.sleep(delay)

    root = tk.Tk()
    root.withdraw()

    # 循环显示弹窗
    for config in popups_config:
        result = False
        if config.get("is_mandatory", False):
            while True:
                response = messagebox.askyesno(title=config.get("title", "提示"), message=config.get("content", ""))
                if response:
                    result = True
                    break
        else:
            result = messagebox.askyesno(title=config.get("title", "提示"), message=config.get("content", ""))

        if result:  # 如果用户点击 "是"
            try:
                # 播放背景音乐
                if music_file and os.path.exists(music_file):
                    pygame.mixer.init()
                    pygame.mixer.music.load(music_file)
                    pygame.mixer.music.set_volume(float(volume))
                    pygame.mixer.music.play(-1)

                # 创建并显示 WebView 窗口
                api = Api()
                window = webview.create_window(' ', html=html_content, fullscreen=True, on_top=True, js_api=api)
                api.set_window(window)
                webview.start()

                # 窗口关闭后停止音乐
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
            except Exception as e:
                messagebox.showerror("错误", f"程序运行出错: {e}")
            return  # 成功后直接退出函数

    # 如果所有弹窗都选择了 "否"，则显示最终拒绝信息
    messagebox.showinfo("提示", final_rejection_text)


# --------------------------------------------------------------------
# 配置程序界面 (Config App UI from 3.py)
# --------------------------------------------------------------------
class ConfessionApp:
    """配置程序的主类"""

    def __init__(self, master):
        self.master = master
        self.master.title("表白程序生成器")
        self.master.geometry("900x750")

        # 确定配置文件路径
        if getattr(sys, 'frozen', False):
            self.application_path = os.path.dirname(sys.executable)
        else:
            self.application_path = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.application_path, "config.json")

        # 初始化默认配置
        self.popups_config = []
        self.html_texts = ['亲爱的', '节日快乐', '我爱你']
        self.heart_text = '我会永远\n陪着你'
        self.music_file = ""
        self.volume = 0.5
        self.delay = 0
        self.final_rejection_text = "好吧，看来你真的不喜欢我..."

        self.load_config()
        self.create_widgets()

    def create_widgets(self):
        # --- UI 布局 ---
        main_frame = Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        top_frame = Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True)

        # --- 左侧面板：HTML 内容设置 ---
        left_panel = Frame(top_frame, relief=tk.GROOVE, borderwidth=2, padx=5, pady=5)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        Label(left_panel, text="成功后显示的文字:", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=5, pady=5)
        html_canvas_frame = Frame(left_panel, height=150)
        html_canvas_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        html_canvas_frame.pack_propagate(False)
        self.html_canvas = Canvas(html_canvas_frame)
        html_scrollbar = Scrollbar(html_canvas_frame, orient="vertical", command=self.html_canvas.yview)
        self.html_scrollable_frame = Frame(self.html_canvas)
        self.html_scrollable_frame.bind("<Configure>",
                                        lambda e: self.html_canvas.configure(scrollregion=self.html_canvas.bbox("all")))
        self.html_canvas.create_window((0, 0), window=self.html_scrollable_frame, anchor="nw")
        self.html_canvas.configure(yscrollcommand=html_scrollbar.set)
        self.html_canvas.pack(side="left", fill="both", expand=True)
        html_scrollbar.pack(side="right", fill="y")
        self.html_entries = []
        self.update_html_entries()
        html_button_frame = Frame(left_panel)
        html_button_frame.pack(fill=tk.X, padx=5, pady=5)
        Button(html_button_frame, text="添加一行文字", command=self.add_html_text).pack(side=tk.LEFT, padx=5)
        Button(html_button_frame, text="移除最后一行", command=self.remove_html_text).pack(side=tk.LEFT, padx=5)
        Label(left_panel, text="心形中间的文字 (可换行):", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=5,
                                                                                                pady=(10, 5))
        self.heart_text_widget = Text(left_panel, height=4, font=("Helvetica", 10))
        self.heart_text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.heart_text_widget.insert(tk.END, self.heart_text)

        # --- 右侧面板：弹窗设置 ---
        right_panel = Frame(top_frame, relief=tk.GROOVE, borderwidth=2, padx=5, pady=5)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        Label(right_panel, text="自定义弹窗内容:", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(5, 0))
        popup_canvas_frame = Frame(right_panel)
        popup_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.popup_canvas = Canvas(popup_canvas_frame)
        popup_scrollbar = Scrollbar(popup_canvas_frame, orient="vertical", command=self.popup_canvas.yview)
        self.popup_scrollable_frame = Frame(self.popup_canvas)
        self.popup_scrollable_frame.bind("<Configure>", lambda e: self.popup_canvas.configure(
            scrollregion=self.popup_canvas.bbox("all")))
        self.popup_canvas.create_window((0, 0), window=self.popup_scrollable_frame, anchor="nw")
        self.popup_canvas.configure(yscrollcommand=popup_scrollbar.set)
        self.popup_canvas.pack(side="left", fill="both", expand=True)
        popup_scrollbar.pack(side="right", fill="y")
        self.popup_widgets = []
        self.update_popup_widgets()
        control_frame = Frame(right_panel)
        control_frame.pack(fill=tk.X, pady=(5, 0))
        Button(control_frame, text="添加一个弹窗", command=self.add_popup_config).pack(side=tk.LEFT, padx=5)
        Button(control_frame, text="移除最后一个弹窗", command=self.remove_popup_config).pack(side=tk.LEFT, padx=5)

        # --- 底部面板：通用设置 ---
        general_settings_frame = Frame(main_frame, relief=tk.GROOVE, borderwidth=2)
        general_settings_frame.pack(fill=tk.X, pady=10)
        Label(general_settings_frame, text="通用设置:", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=5, pady=5)
        rejection_frame = Frame(general_settings_frame)
        rejection_frame.pack(fill=tk.X, padx=10, pady=5)
        Label(rejection_frame, text="最终拒绝信息:").pack(side=tk.LEFT)
        self.rejection_entry = Entry(rejection_frame)
        self.rejection_entry.insert(0, self.final_rejection_text)
        self.rejection_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        delay_frame = Frame(general_settings_frame)
        delay_frame.pack(fill=tk.X, padx=10, pady=5)
        Label(delay_frame, text="弹窗前延迟(秒):").pack(side=tk.LEFT)
        self.delay_entry = Entry(delay_frame, width=10)
        self.delay_entry.insert(0, str(self.delay))
        self.delay_entry.pack(side=tk.LEFT, padx=5)
        music_frame = Frame(general_settings_frame)
        music_frame.pack(fill=tk.X, padx=10, pady=5)
        Label(music_frame, text="背景音乐:").pack(side=tk.LEFT)
        self.music_entry = Entry(music_frame, width=40)
        self.music_entry.insert(0, self.music_file)
        self.music_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        Button(music_frame, text="选择...", command=self.select_music_file).pack(side=tk.LEFT)
        volume_frame = Frame(general_settings_frame)
        volume_frame.pack(fill=tk.X, padx=10, pady=5)
        Label(volume_frame, text="音量大小:").pack(side=tk.LEFT)
        self.volume_slider = Scale(volume_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, length=300)
        self.volume_slider.set(self.volume)
        self.volume_slider.pack(side=tk.LEFT, padx=5)

        # --- 底部按钮 ---
        bottom_frame = Frame(self.master)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        Button(bottom_frame, text="保存并启动", command=self.save_and_launch, bg="#4CAF50", fg="white",
               font=("Helvetica", 12, "bold")).pack(fill=tk.X)

    def select_music_file(self):
        filepath = filedialog.askopenfilename(
            title="选择一个音乐文件",
            filetypes=[("音频文件", "*.mp3 *.wav *.ogg"), ("所有文件", "*.*")]
        )
        if filepath:
            # 尽可能存储相对路径，这对于打包更有利
            try:
                relative_path = os.path.relpath(filepath, self.application_path)
                self.music_file = relative_path
            except ValueError:
                # 如果文件在不同的驱动器上（Windows），则会发生这种情况
                self.music_file = filepath
            self.music_entry.delete(0, tk.END)
            self.music_entry.insert(0, self.music_file)

    def update_html_entries(self):
        for widget in self.html_scrollable_frame.winfo_children():
            widget.destroy()
        self.html_entries = []
        for i, text in enumerate(self.html_texts):
            row_frame = Frame(self.html_scrollable_frame)
            row_frame.pack(fill=tk.X, pady=2, padx=5)
            Label(row_frame, text=f"第 {i + 1} 行:").pack(side=tk.LEFT, padx=5)
            entry = Entry(row_frame, width=40)
            entry.insert(0, text)
            entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
            self.html_entries.append(entry)

    def add_html_text(self):
        self.html_texts.append("新的一行")
        self.update_html_entries()

    def remove_html_text(self):
        if self.html_texts:
            self.html_texts.pop()
            self.update_html_entries()

    def update_popup_widgets(self):
        for widget_dict in self.popup_widgets:
            widget_dict["frame"].destroy()
        self.popup_widgets = []

        for i, config in enumerate(self.popups_config):
            frame = Frame(self.popup_scrollable_frame, relief=tk.RIDGE, borderwidth=2, padx=5, pady=5)
            frame.pack(fill=tk.X, pady=5, padx=5)
            Label(frame, text=f"--- 弹窗 {i + 1} ---", font=("Helvetica", 10, "bold")).grid(row=0, column=0,
                                                                                            columnspan=2, sticky="w")
            Label(frame, text="标题:").grid(row=1, column=0, sticky="w")
            title_entry = Entry(frame, width=50)
            title_entry.insert(0, config.get("title", ""))
            title_entry.grid(row=1, column=1, sticky="ew")
            Label(frame, text="内容:").grid(row=2, column=0, sticky="w")
            content_entry = Entry(frame, width=50)
            content_entry.insert(0, config.get("content", ""))
            content_entry.grid(row=2, column=1, sticky="ew")
            widget_dict = {"frame": frame, "title": title_entry, "content": content_entry}
            if i == len(self.popups_config) - 1:
                mandatory_var = BooleanVar()
                mandatory_var.set(config.get("is_mandatory", False))
                mandatory_check = Checkbutton(frame, text="终极强制 (此弹窗无法关闭，点击确认后直接成功)",
                                              variable=mandatory_var)
                mandatory_check.grid(row=5, column=0, columnspan=2, sticky="w", pady=(5, 0))
                widget_dict["mandatory_var"] = mandatory_var
            frame.columnconfigure(1, weight=1)
            self.popup_widgets.append(widget_dict)

    def add_popup_config(self):
        new_config = {"title": f"问题 {len(self.popups_config) + 1}", "content": "你喜欢我吗？", "is_mandatory": False}
        if self.popups_config:
            self.popups_config[-1]['is_mandatory'] = False
        self.popups_config.append(new_config)
        self.update_popup_widgets()
        self.popup_canvas.update_idletasks()
        self.popup_canvas.yview_moveto(1.0)

    def remove_popup_config(self):
        if self.popups_config:
            self.popups_config.pop()
            self.update_popup_widgets()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.popups_config = config.get("popups", [])
                    self.html_texts = config.get("html_texts", ['亲爱的', '节日快乐', '我爱你'])
                    self.heart_text = config.get("heart_text", '我会永远\n陪着你')
                    self.music_file = config.get("music_file", "")
                    self.volume = config.get("volume", 0.5)
                    self.delay = config.get("delay", 0)
                    self.final_rejection_text = config.get("final_rejection_text", "好吧，看来你真的不喜欢我...")
            except (json.JSONDecodeError, KeyError):
                self.set_default_config()
        else:
            self.set_default_config()

    def set_default_config(self):
        self.popups_config = [
            {"title": "我喜欢你", "content": "做我女朋友好吗？", "is_mandatory": False},
            {"title": "求求你了", "content": "我真的很喜欢你，给我个机会吧", "is_mandatory": False},
        ]
        self.html_texts = ['亲爱的', '节日快乐', '我爱你']
        self.heart_text = '我会永远\n陪着你'
        self.music_file = ""
        self.volume = 0.5
        self.delay = 0
        self.final_rejection_text = "好吧，看来你真的不喜欢我..."

    def get_updated_html_content(self):
        """根据用户配置，在内存中动态修改 HTML 内容"""
        content = HTML_TEMPLATE
        # 替换文字动画的序列
        js_array_str = json.dumps(self.html_texts, ensure_ascii=False)
        content = re.sub(r"simulate\(\[.*\]\);", f"simulate(['#countdown 3', ...{js_array_str}, '#rectangle']);",
                         content)
        # 替换心形中间的文字
        heart_text_html = self.heart_text.replace('\n', '<br>')
        pattern = r'(<div class="heart-text">\s*<h4>)[\s\S]*?(</h4>\s*</div>)'
        replacement = f'\\1&#128151;{heart_text_html}\\2'
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        return content

    def save_and_launch(self):
        """核心函数：保存配置，关闭设置窗口，然后启动主程序"""
        # 1. 从 UI 控件获取所有配置数据
        self.popups_config = []
        for i, widgets in enumerate(self.popup_widgets):
            config = {"title": widgets["title"].get(), "content": widgets["content"].get()}
            if "mandatory_var" in widgets:
                config["is_mandatory"] = widgets["mandatory_var"].get()
            else:
                config["is_mandatory"] = False
            self.popups_config.append(config)

        self.html_texts = [entry.get() for entry in self.html_entries]
        self.heart_text = self.heart_text_widget.get("1.0", tk.END).strip()
        self.music_file = self.music_entry.get()
        self.volume = self.volume_slider.get()
        try:
            self.delay = int(self.delay_entry.get())
        except ValueError:
            self.delay = 0
        self.final_rejection_text = self.rejection_entry.get()

        # 2. 组合成一个字典
        config_data = {
            "popups": self.popups_config,
            "html_texts": self.html_texts,
            "heart_text": self.heart_text,
            "music_file": self.music_file,
            "volume": self.volume,
            "delay": self.delay,
            "final_rejection_text": self.final_rejection_text
        }

        # 3. 将配置数据写入 config.json 文件
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("错误", f"无法保存配置文件: {e}")
            return

        # 4. 获取更新后的 HTML 内容
        final_html = self.get_updated_html_content()

        # 5. 销毁配置窗口
        self.master.destroy()

        # 6. 使用更新后的 HTML 内容启动主表白程序
        show_confession(html_content=final_html)


# --------------------------------------------------------------------
# 程序入口 (Application Entry Point)
# --------------------------------------------------------------------
if __name__ == "__main__":
    # 启动时总是先显示配置窗口
    root = tk.Tk()
    app = ConfessionApp(root)
    root.mainloop()
