import tkinter as tk
from tkinter import ttk

from ..domain.validation import validate_pin
from .widgets import heading, make_entry


class LoginScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="Card.TFrame", padding=28)
        self.controller = controller
        self.account_var = tk.StringVar(master=self)
        self.pin_var = tk.StringVar(master=self)
        self.warning_var = tk.StringVar(master=self)
        heading(self, "ATM에 오신 것을 환영합니다", "가상 계좌로 로그인하고 입금·출금·이체를 이용해 보세요.")
        body = ttk.Frame(self, style="Card.TFrame")
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        guide = ttk.Frame(body, style="Soft.TFrame", padding=24)
        guide.grid(row=0, column=0, sticky="nsew", padx=(0, 28))
        ttk.Label(guide, text="가볍게 시작하는\n나의 ATM", style="SoftHeading.TLabel").pack(anchor="w", pady=(0, 20))
        ttk.Label(guide, text="01  가상 계좌로 로그인\n\n02  원하는 거래 선택\n\n03  결과 확인 후 종료", style="Soft.TLabel", justify="left").pack(anchor="w")
        ttk.Label(guide, text="학습용 시뮬레이터입니다.\n실제 은행과 연결되지 않습니다.", style="Soft.TLabel", justify="left").pack(side="bottom", anchor="w", pady=(28, 0))
        form = ttk.Frame(body, style="Card.TFrame")
        form.grid(row=0, column=1, sticky="nsew")
        ttk.Label(form, text="가상 계좌번호").pack(anchor="w", pady=(0, 8))
        self.account_entry = make_entry(form, self.account_var)
        self.account_entry.pack(fill="x")
        ttk.Label(form, text="숫자 12자리", style="Small.TLabel").pack(anchor="w", pady=(6, 18))
        ttk.Label(form, text="비밀번호 (PIN)").pack(anchor="w", pady=(0, 8))
        self.pin_entry = make_entry(form, self.pin_var, pin=True)
        self.pin_entry.pack(fill="x")
        ttk.Label(form, text="숫자 4자리 · 연속 5회 오류 시 계좌 차단", style="Small.TLabel").pack(anchor="w", pady=(6, 12))
        ttk.Label(form, textvariable=self.warning_var, style="Error.TLabel", wraplength=480).pack(anchor="w", fill="x", pady=(0, 14))
        self.login_button = ttk.Button(form, text="로그인", style="Primary.TButton", command=self.submit)
        self.login_button.pack(fill="x")
        ttk.Label(form, text="체험 계좌: 100100000001\n가상 PIN과 다른 체험 계좌는 README.md에서 확인하세요.", style="Small.TLabel", wraplength=470).pack(anchor="w", pady=(20, 0))

    def submit(self) -> None:
        self.controller.request_login(self.account_var.get(), self.pin_var.get())

    def show(self) -> None:
        """OP-08."""
        self.account_var.set("")
        self.pin_var.set("")
        self.warning_var.set("")
        self.controller.show_page("login")
        self.account_entry.focus_set()

    @staticmethod
    def validate_pin(password: str) -> bool:
        """OP-09."""
        return validate_pin(password)

    def show_warning(self, message: str) -> None:
        """OP-10."""
        self.pin_var.set("")
        self.warning_var.set(message)
        self.pin_entry.focus_set()
