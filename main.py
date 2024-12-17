# python -m pip install pyinstaller customtkinter sounddevice numpy
# pyinstaller --onefile --windowed main.py
from tkinter import messagebox
import customtkinter as ctk
import sounddevice as sd
import numpy as np
import wave
import os
import time

class TTSRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("TTS Dataset Recorder")
        self.sentences = self.load_sentences("./dialog.txt")
        self.current_index = 0
        self.progress_label = ctk.CTkLabel(root, text=self.get_progress_text(), font=("맑은 고딕", 18))
        self.progress_label.pack(pady=10)
        self.label = ctk.CTkLabel(root, text=self.sentences[self.current_index], wraplength=500, font=("맑은 고딕", 24), height=80)
        self.label.pack(pady=20)
        self.status_label = ctk.CTkLabel(root, text="상태: 대기 중\n", font=("맑은 고딕", 16))
        self.status_label.pack(pady=10)
        device_frame = ctk.CTkFrame(root)
        device_frame.pack(pady=5)
        self.device_label = ctk.CTkLabel(device_frame, text="입력 장치 선택:", font=("맑은 고딕", 16))
        self.device_label.pack(side=ctk.LEFT, padx=5)
        self.device_list = [device["name"] for device in sd.query_devices() if device["max_input_channels"] > 0]
        self.device_var = ctk.StringVar(value=self.device_list[0])
        self.device_menu = ctk.CTkOptionMenu(master=device_frame, values=self.device_list, variable=self.device_var)
        self.device_menu.pack(side=ctk.LEFT, padx=5)
        self.device_menu.set(self.device_list[0])
        button_frame = ctk.CTkFrame(root)
        button_frame.pack(pady=10)
        self.prev_button = ctk.CTkButton(button_frame, text="이전", command=self.prev_sentence)
        self.prev_button.pack(side=ctk.LEFT, padx=10)
        self.play_button = ctk.CTkButton(button_frame, text="재생", command=self.play_recording)
        self.play_button.pack(side=ctk.LEFT, padx=10)
        self.next_button = ctk.CTkButton(button_frame, text="다음", command=self.next_sentence)
        self.next_button.pack(side=ctk.LEFT, padx=10)
        self.record_button = ctk.CTkButton(button_frame, text="녹음 시작/정지", command=self.toggle_recording)
        self.record_button.pack(side=ctk.LEFT, padx=10)
        self.update_sentence_label_color()
        self.is_recording = False
        self.frames = []
        self.start_time = None
        if not os.path.exists("./recorded"):
            os.makedirs("./recorded")
        self.root.bind("<KeyPress-space>", self.start_recording)
        self.root.bind("<KeyPress-Up>", self.start_recording)
        self.root.bind("<KeyRelease-space>", self.stop_recording)
        self.root.bind("<KeyRelease-Up>", self.stop_recording)
        self.root.bind("<KeyPress-Down>", self.play_recording)
        self.root.bind("<Left>", self.prev_sentence)
        self.root.bind("<Return>", self.next_sentence)
        self.root.bind("<Right>", self.next_sentence)
        self.shortcut_label = ctk.CTkLabel(root, text="단축키: 녹음 시작/정지: ↑ 또는 Space, 재생: ↓, 이전: ←, 다음: → 또는 Enter", font=("맑은 고딕", 12), text_color="gray")
        self.shortcut_label.pack()
        self.notice_label = ctk.CTkLabel(root, text="[고품질 데이터셋을 만들기 위한 팁]\n1. 되도록 마이크 가까이에서, 조용한 환경에서 녹음하기\n2. 모든 문장은 일정하고 명료하게 발음하기\n3. 문장 부호(?!.,)의 톤을 강조하기\n4. 문장 시작과 끝을 잘라먹지 않도록 주의하기", font=("맑은 고딕", 12), text_color="gray")
        self.notice_label.pack()

    def update_sentence_label_color(self):
        filename = f"./recorded/sentence_{self.current_index + 1}.wav"
        if os.path.exists(filename):
            self.label.configure(text_color="green")
            self.play_button.configure(state=ctk.NORMAL)
        else:
            self.label.configure(text_color="white")
            self.play_button.configure(state=ctk.DISABLED)

    def load_sentences(self, filepath):
        with open(filepath, "r", encoding="utf-8") as file:
            sentences = file.readlines()
        return [sentence.strip() for sentence in sentences]

    def get_progress_text(self):
        total = len(self.sentences)
        current = self.current_index + 1
        percent = (current / total) * 100
        return f"현재 문장: {current} / {total} ({percent:.2f}%)"

    def update_progress(self):
        self.progress_label.configure(text=self.get_progress_text())

    def prev_sentence(self, event=None):
        if self.current_index > 0:
            self.current_index -= 1
            self.label.configure(text=self.sentences[self.current_index])
            self.update_progress()
            self.update_sentence_label_color()
            self.status_label.configure(text="상태: 대기 중\n")

    def next_sentence(self, event=None):
        if self.current_index < len(self.sentences) - 1:
            self.current_index += 1
            self.label.configure(text=self.sentences[self.current_index])
            self.update_progress()
            self.update_sentence_label_color()
            self.status_label.configure(text="상태: 대기 중\n")

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self, event=None):
        if not self.is_recording:
            self.is_recording = True
            self.frames = []
            self.start_time = time.time()
            self.status_label.configure(text="녹음 중: 00:00:00\n")
            device_index = self.device_list.index(self.device_var.get())
            self.stream = sd.InputStream(callback=self.callback, channels=1, samplerate=44100, device=device_index)
            self.stream.start()

    def callback(self, indata, frames, callback_time, status):
        if self.is_recording:
            self.frames.append(indata.copy())
            elapsed_time = time.time() - self.start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            milliseconds = int((elapsed_time - int(elapsed_time)) * 100)
            self.status_label.configure(text=f"녹음 중: {minutes:02}:{seconds:02}.{milliseconds:02}\n")

    def stop_recording(self, event=None):
        if self.is_recording:
            self.is_recording = False
            self.stream.stop()
            self.stream.close()
            if self.frames:
                filename = self.save_recording()
                self.status_label.configure(text="상태: 녹음 완료, 저장됨\n" + filename)
            else:
                self.status_label.configure(text="상태: 녹음 실패 (녹음된 데이터 없음)\n단축키를 누르고 있는 동안에만 녹음됩니다.")
            self.update_sentence_label_color()

    def save_recording(self):
        filename = f"./recorded/sentence_{self.current_index + 1}.wav"
        wf = wave.open(filename, "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        frames_array = np.concatenate(self.frames, axis=0)
        frames_array = np.int16(frames_array * 32767)
        wf.writeframes(frames_array.tobytes())
        wf.close()
        return filename

    def play_recording(self, event=None):
        filename = f"./recorded/sentence_{self.current_index + 1}.wav"
        if os.path.exists(filename):
            status_window = ctk.CTkToplevel(self.root)
            status_window.title("재생 상태")
            status_label = ctk.CTkLabel(status_window, text="재생 준비 중...", font=("맑은 고딕", 16))
            status_label.pack(padx=20, pady=20)
            wf = wave.open(filename, "rb")
            samplerate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())
            total_frames = wf.getnframes()
            duration = total_frames / samplerate
            slider = ctk.CTkSlider(master=status_window, from_=0, to=duration)
            slider.pack(padx=20, pady=20)
            wf.close()
            frames_array = np.frombuffer(frames, dtype=np.int16)
            sd.play(frames_array, samplerate)
            start_time = time.time()

            def update_status():
                if sd.get_stream().active:
                    elapsed_time = time.time() - start_time
                    percent = min((elapsed_time / duration) * 100, 100)
                    status_label.configure(text=f"{int(elapsed_time//60):02}:{int(elapsed_time%60):02}/{int(duration//60):02}:{int(duration%60):02} ({int(percent)}%)")
                    slider.set(elapsed_time)
                    status_window.after(10, update_status)
                else:
                    status_window.after(100, status_window.destroy)

            update_status()
        else:
            messagebox.showwarning("파일 없음", "녹음된 파일이 없습니다.")

if __name__ == "__main__":
    root = ctk.CTk()
    root.eval("tk::PlaceWindow . center")
    app = TTSRecorder(root)
    root.mainloop()
