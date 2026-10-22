import random
import tkinter as tk
from datetime import datetime

SET_COUNT = 5      # 세트 수
NUM_COUNT = 6      # 세트당 숫자 개수
BALL_SIZE = 44     # 공 지름(px)


def ball_color(n):
    """동행복권 공 색상 규칙"""
    if n <= 10:
        return "#FBC400"   # 노랑
    elif n <= 20:
        return "#69C8F2"   # 파랑
    elif n <= 30:
        return "#FF7272"   # 빨강
    elif n <= 40:
        return "#AAAAAA"   # 회색
    else:
        return "#B0D840"   # 초록


def make_numbers():
    """1~45 중 중복 없이 6개를 뽑아 정렬"""
    return sorted(random.sample(range(1, 46), NUM_COUNT))


def draw_ball(canvas, x, y, n):
    color = ball_color(n)
    canvas.create_oval(x, y, x + BALL_SIZE, y + BALL_SIZE, fill=color, outline="")
    canvas.create_text(
        x + BALL_SIZE / 2, y + BALL_SIZE / 2,
        text=str(n), fill="white", font=("맑은 고딕", 14, "bold"),
    )


def generate():
    now = datetime.now()
    date_label.config(text=now.strftime("%Y년 %m월 %d일 %H:%M:%S 생성"))

    canvas.delete("all")
    gap = 10
    for i in range(SET_COUNT):
        y = 15 + i * (BALL_SIZE + 18)
        # 세트 이름 (A~E)
        canvas.create_text(25, y + BALL_SIZE / 2, text=chr(65 + i),
                           font=("맑은 고딕", 14, "bold"), fill="#333")
        for j, n in enumerate(make_numbers()):
            x = 55 + j * (BALL_SIZE + gap)
            draw_ball(canvas, x, y, n)


# ---------------- 화면 구성 ----------------
root = tk.Tk()
root.title("로또 번호 생성기")
root.geometry("420x480")
root.resizable(False, False)
root.configure(bg="white")

title_label = tk.Label(root, text="🎱 로또 6/45 번호 생성기",
                       font=("맑은 고딕", 18, "bold"), bg="white")
title_label.pack(pady=(15, 5))

date_label = tk.Label(root, text=datetime.now().strftime("%Y년 %m월 %d일"),
                      font=("맑은 고딕", 11), fg="#666", bg="white")
date_label.pack()

canvas = tk.Canvas(root, width=400, height=320, bg="white", highlightthickness=0)
canvas.pack(pady=10)
canvas.create_text(200, 160, text="아래 버튼을 눌러 번호를 생성하세요",
                   font=("맑은 고딕", 12), fill="#999")

button = tk.Button(root, text="번호 생성", font=("맑은 고딕", 14, "bold"),
                   bg="#4A6CF7", fg="white", activebackground="#3451C6",
                   activeforeground="white", relief="flat",
                   padx=20, pady=6, command=generate)
button.pack()

root.mainloop()
