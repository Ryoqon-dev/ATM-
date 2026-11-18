"""Shared visual helpers; these functions contain no account mutations."""
import tkinter as tk
from tkinter import font as tkfont, ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .transaction_screen import TransactionScreen

NAVY = "#172E4D"
BLUE = "#2261A5"
BACKGROUND = "#F3F6FB"
MUTED = "#65758A"


def configure_theme(root: tk.Tk) -> None:
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        tkfont.nametofont(name).configure(family="맑은 고딕", size=10)
    root.configure(background=BACKGROUND)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("App.TFrame", background=BACKGROUND)
    style.configure("Card.TFrame", background="white")
    style.configure("Soft.TFrame", background="#EDF4FB")
    style.configure("Header.TFrame", background=NAVY)
    style.configure("TLabel", background="white", foreground=NAVY, font=("맑은 고딕", 10))
    style.configure("Muted.TLabel", foreground=MUTED)
    style.configure("Small.TLabel", foreground=MUTED, font=("맑은 고딕", 9))
    style.configure("Title.TLabel", font=("맑은 고딕", 22, "bold"))
    style.configure("Heading.TLabel", font=("맑은 고딕", 14, "bold"))
    style.configure("Balance.TLabel", font=("맑은 고딕", 34, "bold"), foreground=BLUE)
    style.configure("Soft.TLabel", background="#EDF4FB", foreground=NAVY)
    style.configure("SoftHeading.TLabel", background="#EDF4FB", foreground=BLUE, font=("맑은 고딕", 13, "bold"))
    style.configure("Header.TLabel", background=NAVY, foreground="white", font=("맑은 고딕", 19, "bold"))
    style.configure("HeaderSmall.TLabel", background=NAVY, foreground="#D4E4F5", font=("맑은 고딕", 10))
    style.configure("Footer.TLabel", background=BACKGROUND, foreground=MUTED, font=("맑은 고딕", 9))
    style.configure("Error.TLabel", foreground="#B4233A", font=("맑은 고딕", 10))
    style.configure("Success.TLabel", foreground="#18724A", font=("맑은 고딕", 14, "bold"))
    style.configure("Primary.TButton", background=BLUE, foreground="white", padding=(18, 13), font=("맑은 고딕", 11, "bold"), borderwidth=0)
    style.map("Primary.TButton", background=[("disabled", "#C5CEDB"), ("active", "#194E88")], foreground=[("disabled", "#F4F6F9")])
    style.configure("Secondary.TButton", background="#EDF2F8", foreground=NAVY, padding=(16, 12), font=("맑은 고딕", 10), borderwidth=0)
    style.map("Secondary.TButton", background=[("active", "#DDE8F4"), ("disabled", "#F0F2F6")])
    style.configure("Quick.TButton", background="#F2F6FB", foreground=BLUE, padding=(12, 8), font=("맑은 고딕", 10), borderwidth=0)
    style.map("Quick.TButton", background=[("active", "#E0EBF8")])
    style.configure("Field.TEntry", fieldbackground="white", foreground=NAVY, padding=(12, 10), bordercolor="#CCD7E5", lightcolor="#CCD7E5", darkcolor="#CCD7E5")
    style.map("Field.TEntry", bordercolor=[("focus", BLUE)])
    style.configure("Horizontal.TProgressbar", background=BLUE, troughcolor="#EDF2F8", borderwidth=0)


def heading(parent, title: str, subtitle: str) -> None:
    ttk.Label(parent, text=title, style="Title.TLabel").pack(anchor="w")
    ttk.Label(parent, text=subtitle, style="Muted.TLabel", wraplength=780).pack(anchor="w", pady=(8, 24))


def make_entry(parent, variable: tk.StringVar, *, pin: bool = False) -> ttk.Entry:
    return ttk.Entry(parent, textvariable=variable, style="Field.TEntry", font=("맑은 고딕", 16), show="●" if pin else "")


def setup_transaction(screen, controller: "TransactionScreen", kind: str, title: str, subtitle: str) -> None:
    """The three financial screens use the same accessible form/result layout."""
    screen.controller = controller
    screen.kind = kind
    screen.stage = "input"
    screen.amount_var = tk.StringVar(master=screen)
    screen.target_var = tk.StringVar(master=screen)
    screen.balance_var = tk.StringVar(master=screen)
    screen.message_var = tk.StringVar(master=screen)
    screen.result_title_var = tk.StringVar(master=screen)
    screen.result_balance_var = tk.StringVar(master=screen)
    screen.result_detail_var = tk.StringVar(master=screen)
    screen.receipt_var = tk.StringVar(master=screen)
    screen.result_success = False
    screen.result_balance = None
    screen.result_amount = 0
    heading(screen, title, subtitle)
    ttk.Label(screen, textvariable=screen.balance_var, style="Heading.TLabel").pack(anchor="w", pady=(0, 20))

    screen.form = ttk.Frame(screen, style="Card.TFrame")
    screen.form.pack(fill="both", expand=True)
    screen.input_widgets = []
    if kind == "transfer":
        ttk.Label(screen.form, text="이체 대상 계좌번호").pack(anchor="w", pady=(0, 7))
        screen.target_entry = make_entry(screen.form, screen.target_var)
        screen.target_entry.pack(fill="x", pady=(0, 15))
        screen.input_widgets.append(screen.target_entry)
    ttk.Label(screen.form, text="거래 금액 (원)").pack(anchor="w", pady=(0, 7))
    screen.amount_entry = make_entry(screen.form, screen.amount_var)
    screen.amount_entry.pack(fill="x")
    screen.input_widgets.append(screen.amount_entry)
    ttk.Label(screen.form, text="쉼표와 공백 없이 숫자만 입력해 주세요.", style="Small.TLabel").pack(anchor="w", pady=(7, 14))
    quick = ttk.Frame(screen.form, style="Card.TFrame")
    quick.pack(fill="x", pady=(0, 22))
    ttk.Label(quick, text="바로 입력", style="Small.TLabel").pack(side="left", padx=(0, 12))
    for value in (10_000, 50_000, 100_000, 1_000_000):
        button = ttk.Button(quick, text=f"{value // 10000}만 원", style="Quick.TButton", command=lambda amount=value: screen.amount_var.set(str(amount)))
        button.pack(side="left", padx=(0, 8))
        screen.input_widgets.append(button)
    screen.status_label = ttk.Label(screen.form, textvariable=screen.message_var, style="Muted.TLabel", wraplength=780)
    screen.status_label.pack(anchor="w", pady=(0, 10))
    screen.progress = ttk.Progressbar(screen.form, mode="indeterminate", length=240)
    screen.actions = ttk.Frame(screen.form, style="Card.TFrame")
    screen.actions.pack(side="bottom", fill="x", pady=(18, 0))
    command = {
        "deposit": lambda: controller.request_deposit(screen.amount_var.get()),
        "withdrawal": lambda: controller.request_withdrawal(screen.amount_var.get()),
        "transfer": lambda: controller.request_transfer(screen.target_var.get(), screen.amount_var.get()),
    }[kind]
    screen.confirm_button = ttk.Button(screen.actions, text="거래 확인", command=command, style="Primary.TButton")
    screen.confirm_button.pack(side="right")
    screen.cancel_button = ttk.Button(screen.actions, text="취소하고 메뉴로", command=lambda: controller.select_menu("menu"), style="Secondary.TButton")
    screen.cancel_button.pack(side="right", padx=(0, 10))
    screen.input_widgets += [screen.confirm_button, screen.cancel_button]

    screen.result = ttk.Frame(screen, style="Card.TFrame")
    screen.result_heading = ttk.Label(screen.result, textvariable=screen.result_title_var, style="Success.TLabel")
    screen.result_heading.pack(anchor="w", pady=(12, 15))
    ttk.Label(screen.result, textvariable=screen.message_var, wraplength=780).pack(anchor="w", pady=(0, 15))
    ttk.Label(screen.result, textvariable=screen.result_detail_var, style="Muted.TLabel").pack(anchor="w", pady=(0, 14))
    ttk.Label(screen.result, text="현재 잔액", style="Muted.TLabel").pack(anchor="w")
    ttk.Label(screen.result, textvariable=screen.result_balance_var, style="Balance.TLabel").pack(anchor="w", pady=(5, 16))
    screen.receipt_frame = ttk.Frame(screen.result, style="Soft.TFrame", padding=14)
    ttk.Label(screen.receipt_frame, textvariable=screen.receipt_var, style="Soft.TLabel", wraplength=730).pack(anchor="w")
    screen.receipt_actions = ttk.Frame(screen.receipt_frame, style="Soft.TFrame")
    screen.receipt_actions.pack(anchor="w", pady=(10, 0))
    for label, choice in (("예", True), ("아니오", False)):
        ttk.Button(screen.receipt_actions, text=label, style="Quick.TButton", command=lambda selected=choice: choose_receipt(screen, selected)).pack(side="left", padx=(0, 10))
    screen.result_actions = ttk.Frame(screen.result, style="Card.TFrame")
    screen.result_actions.pack(side="bottom", fill="x", pady=(20, 0))
    screen.continue_button = ttk.Button(screen.result_actions, text="계속 이용하기", style="Primary.TButton", command=lambda: controller.select_menu("menu"))
    screen.continue_button.pack(side="right")
    screen.end_button = ttk.Button(screen.result_actions, text="거래 종료", style="Secondary.TButton", command=controller.end_session)
    screen.end_button.pack(side="right", padx=(0, 10))


def choose_receipt(screen, selected: bool) -> None:
    if screen.stage != "result" or not screen.result_success:
        return
    screen.receipt_var.set("명세표 출력 요청을 확인했습니다. 이 시뮬레이터는 실제 인쇄를 제공하지 않습니다." if selected else "명세표를 출력하지 않습니다. 계속 이용하거나 거래를 종료해 주세요.")
    screen.receipt_actions.pack_forget()
    screen.continue_button.configure(state="normal")
    screen.end_button.configure(state="normal")


def lock_form(screen, busy: bool) -> None:
    for widget in screen.input_widgets:
        widget.configure(state="disabled" if busy else "normal")
    if busy:
        screen.progress.pack(anchor="w", pady=(2, 8))
        screen.progress.start(12)
    else:
        screen.progress.stop()
        screen.progress.pack_forget()


def reset_transaction(screen) -> None:
    lock_form(screen, False)
    for variable in (screen.amount_var, screen.target_var, screen.balance_var, screen.message_var,
                     screen.result_title_var, screen.result_balance_var, screen.result_detail_var, screen.receipt_var):
        variable.set("")
    screen.result_success = False
    screen.result_balance = None
    screen.result_amount = 0
    screen.stage = "input"
    screen.receipt_frame.pack_forget()
    screen.result.pack_forget()
    screen.form.pack(fill="both", expand=True)
    screen.continue_button.configure(state="normal")
    screen.end_button.configure(state="normal")


def show_transaction(screen) -> None:
    reset_transaction(screen)
    balance = screen.controller.screen_data.shown_balance
    screen.balance_var.set(f"이용 가능 잔액  {balance:,}원" if balance is not None else "")
    screen.controller.show_page(screen.kind)
    (screen.target_entry if screen.kind == "transfer" else screen.amount_entry).focus_set()


def show_transaction_result(screen, message: str) -> None:
    lock_form(screen, False)
    screen.stage = "result"
    screen.amount_var.set("")
    screen.target_var.set("")
    screen.message_var.set(message)
    screen.result_title_var.set("거래가 완료되었습니다" if screen.result_success else "거래가 취소되었습니다")
    screen.result_heading.configure(style="Success.TLabel" if screen.result_success else "Heading.TLabel")
    screen.result_detail_var.set(f"거래 금액  {screen.result_amount:,}원" if screen.result_success else "계좌 잔액은 변경되지 않았습니다.")
    screen.result_balance_var.set(f"{screen.result_balance:,}원" if screen.result_balance is not None else "—")
    screen.balance_var.set("")
    screen.form.pack_forget()
    screen.result.pack(fill="both", expand=True)
    screen.controller.show_page(screen.kind)
    screen.continue_button.focus_set()
