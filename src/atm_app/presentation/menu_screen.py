import tkinter as tk
from tkinter import ttk

from .widgets import heading


class MenuScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="Card.TFrame", padding=28)
        self.controller = controller
        self.balance_var = tk.StringVar(master=self)
        self.account_var = tk.StringVar(master=self)
        self.warning_var = tk.StringVar(master=self)
        heading(self, "어떤 거래를 도와드릴까요?", "거래가 끝나면 종료 버튼을 눌러 화면의 계좌 정보를 지워 주세요.")
        ttk.Label(self, textvariable=self.account_var, style="Muted.TLabel").pack(anchor="w")
        ttk.Label(self, text="현재 계좌 잔액", style="Muted.TLabel").pack(anchor="w", pady=(20, 4))
        ttk.Label(self, textvariable=self.balance_var, style="Balance.TLabel").pack(anchor="w", pady=(0, 28))
        actions = ttk.Frame(self, style="Card.TFrame")
        actions.pack(fill="x")
        self.buttons = {}
        for i, (kind, label, detail) in enumerate((
            ("deposit", "입금하기", "1회 최대 100만 원"),
            ("withdrawal", "출금하기", "1만 원 단위 · 최대 100만 원"),
            ("transfer", "가상 이체", "송신 계좌에서만 차감"),
        )):
            actions.columnconfigure(i, weight=1, uniform="action")
            card = ttk.Frame(actions, style="Soft.TFrame", padding=18)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            button = ttk.Button(card, text=label, style="Primary.TButton", command=lambda choice=kind: controller.select_menu(choice))
            button.pack(fill="x")
            self.buttons[kind] = button
            ttk.Label(card, text=detail, style="Soft.TLabel", wraplength=220).pack(anchor="w", pady=(12, 0))
        ttk.Label(self, textvariable=self.warning_var, style="Error.TLabel", wraplength=780).pack(anchor="w", pady=16)
        self.end_button = ttk.Button(self, text="거래 종료", style="Secondary.TButton", command=controller.end_session)
        self.end_button.pack(side="bottom", anchor="e", pady=(18, 0))

    def show(self, balance: int) -> None:
        """OP-11."""
        self.balance_var.set(f"{balance:,}원")
        self.account_var.set(f"이용 계좌  {self.controller.screen_data.account_number}")
        self.warning_var.set("")
        self.controller.show_page("menu")

    def clear(self) -> None:
        self.balance_var.set("")
        self.account_var.set("")
        self.warning_var.set("")
