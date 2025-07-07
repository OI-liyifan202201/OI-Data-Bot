import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledText
from tkinter import messagebox
import openai
import subprocess
import os
import threading
import time
import zipfile

class DataGeneratorApp:
    def __init__(self, master):
        self.master = master
        master.title("[GSML] 数据生成器")
        master.geometry("700x600")

        # 创建界面组件
        self.create_widgets()
        
        # 初始化状态
        self.is_running = False

    def create_widgets(self):
        # 输入区域框架
        input_frame = ttk.Labelframe(self.master, text="配置参数", bootstyle="info")
        input_frame.pack(padx=10, pady=5, fill=ttk.BOTH)

        # 题面描述
        ttk.Label(input_frame, text="题面描述:").grid(row=0, column=0, sticky="w", padx=5)
        self.problem_desc = ScrolledText(input_frame, width=80, height=10, bootstyle="default")
        self.problem_desc.grid(row=0, column=1, pady=5, padx=5)

        # API密钥
        ttk.Label(input_frame, text="API密钥:").grid(row=1, column=0, sticky="w", padx=5)
        self.api_key_entry = ttk.Entry(input_frame, width=50, bootstyle="default")
        self.api_key_entry.insert(0, "sk-sLUVtvFrlmzGZu1ZE3F4D2462dFe48Bc9f3c9aFd000dE701")
        self.api_key_entry.grid(row=1, column=1, sticky="w", pady=2)

        # GPT服务器
        ttk.Label(input_frame, text="GPT服务器:").grid(row=2, column=0, sticky="w", padx=5)
        self.gpt_server_entry = ttk.Entry(input_frame, width=50, bootstyle="default")
        self.gpt_server_entry.insert(0, "https://free.v36.cm/v1/")
        self.gpt_server_entry.grid(row=2, column=1, sticky="w", pady=2)

        # 数据组数
        ttk.Label(input_frame, text="数据组数:").grid(row=3, column=0, sticky="w", padx=5)
        self.num_cases_entry = ttk.Entry(input_frame, width=10, bootstyle="default")
        self.num_cases_entry.insert(0, "10")
        self.num_cases_entry.grid(row=3, column=1, sticky="w", pady=2)

        # 控制按钮
        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(pady=5)
        self.generate_btn = ttk.Button(btn_frame, text="开始生成", command=self.toggle_generation, bootstyle="success")
        self.generate_btn.pack(side=ttk.LEFT, padx=5)

        # 日志输出
        log_frame = ttk.Labelframe(self.master, text="生成日志", bootstyle="info")
        log_frame.pack(padx=10, pady=5, fill=ttk.BOTH, expand=True)
        self.log = ScrolledText(log_frame, width=100, height=20, bootstyle="default")
        self.log.pack(fill=ttk.BOTH, expand=True)

    def log_message(self, message):
        self.log.insert(ttk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log.see(ttk.END)
    
    def toggle_generation(self):
        if self.is_running:
            self.is_running = False
            self.generate_btn.config(text="开始生成", bootstyle="success")
        else:
            self.is_running = True
            self.generate_btn.config(text="停止生成", bootstyle="danger")
            thread = threading.Thread(target=self.generate_process)
            thread.start()

    def generate_process(self):
        try:
            # 获取输入参数
            problem_text = self.problem_desc.get("1.0", ttk.END).strip()
            api_key = self.api_key_entry.get().strip()
            gpt_server = self.gpt_server_entry.get().strip()
            num_cases = int(self.num_cases_entry.get().strip())

            # 验证输入
            if not all([problem_text, api_key, gpt_server, num_cases > 0]):
                raise ValueError("请填写所有必要参数")
            os.system("echo y | rd /s test")  
            os.system("md test")
            
            # 配置OpenAI
            openai.api_key = api_key
            openai.base_url = gpt_server
            openai.default_headers = {"x-foo": "true"}

            # 生成CYaRon脚本
            self.log_message("正在通过GPT生成数据生成脚本...")
            prompt = f"""请根据以下题目描述生成随机数据生成脚本：
0. (最重要的). 只用按照输入格式输出（就是一般题面中的## 输入格式"），不要写多余的内容（如解决代码）
1. 每次运行生成一组数据
2. 输出到output.in文件
3. 使用Python编写
4. 仅输出代码，不要注释
5. 请尽量不要使用任何外部库
题目描述：
{problem_text}"""
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            
            code = response.choices[0].message.content
            code = code.replace("```python", "").replace("```", "").strip()
            
            with open("ask.py", "w", encoding="utf-8") as f:
                f.write(code)
            
            self.log_message("脚本生成成功，正在验证...")

            # 验证脚本有效性
            try:
                subprocess.run(
                    ["python", "ask.py"],
                    check=True,
                    timeout=5,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE
                )
                if not os.path.exists("output.in"):
                    raise RuntimeError("脚本未生成输出文件")
                os.remove("output.in")
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"脚本执行失败: {e.stderr.decode().strip()}")


            # 检查并编译 std.exe
            if not os.path.exists("std.exe"):
                self.log_message("std.exe 不存在，尝试编译 std.cpp...")
                if os.path.exists("std.cpp"):
                    try:
                        subprocess.run(
                            ["g++", "std.cpp", "-o", "std.exe"],
                            check=True,
                            timeout=10,
                            stderr=subprocess.PIPE
                        )
                        self.log_message("std.cpp 编译成功")
                    except subprocess.CalledProcessError as e:
                        raise RuntimeError(f"std.cpp 编译失败: {e.stderr.decode().strip()}")
                else:
                    raise FileNotFoundError("std.cpp 不存在，无法生成 std.exe")


            # 准备测试目录
            test_dir = "test"
            os.makedirs(test_dir, exist_ok=True)

            # 生成测试数据
            self.log_message(f"开始生成 {num_cases} 组测试数据...")
            for i in range(1, num_cases+1):
                if not self.is_running:
                    break

                try:
                    # 生成输入
                    subprocess.run(
                        ["python", "ask.py"],
                        check=True,
                        timeout=5,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE
                    )
                    os.rename("output.in", os.path.join(test_dir, f"{i}.in"))

                    # 生成输出
                    with open(os.path.join(test_dir, f"{i}.in"), "r") as fin:
                        with open(os.path.join(test_dir, f"{i}.out"), "w") as fout:
                            subprocess.run(
                                ["std.exe"],
                                stdin=fin,
                                stdout=fout,
                                check=True,
                                timeout=5,
                                stderr=subprocess.PIPE
                            )
                    
                    self.log_message(f"成功生成第 {i} 组数据")

                except subprocess.CalledProcessError as e:
                    self.log_message(f"生成失败: {e.stderr.decode().strip()}")
                except Exception as e:
                    self.log_message(f"发生错误: {str(e)}")

            if self.is_running:
                messagebox.showinfo("完成", "数据生成完成！")
                self.log_message("全部数据生成完毕")
                with zipfile.ZipFile('data.zip', 'w') as zipf:
                    for i in range(1, num_cases+1):
                        in_file = os.path.join(test_dir, f"{i}.in")
                        out_file = os.path.join(test_dir, f"{i}.out")
                        if os.path.exists(in_file) and os.path.exists(out_file):
                            zipf.write(in_file, f"{i}.in")
                            zipf.write(out_file, f"{i}.out")
                    
                os.system("echo y | rd /s test")  
                os.system("del ask.py")
                self.log_message("数据已压缩到 data.zip")

        except Exception as e:
            messagebox.showerror("错误", str(e))
            self.log_message(f"错误: {str(e)}")
        finally:
            self.is_running = False
            self.master.after(0, lambda: self.generate_btn.config(text="开始生成"))

if __name__ == "__main__":
    root = ttk.tk.Tk()
    app = DataGeneratorApp(root)
    root.mainloop()
