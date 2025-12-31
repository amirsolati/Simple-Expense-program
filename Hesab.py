import pandas as pd
import os
import tkinter as tk
from tkinter import messagebox, ttk
import hashlib
from datetime import datetime

FILE_NAME = "data.xlsx"

# -------------------------------
# هش کردن رمز عبور
# -------------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# -------------------------------
# آماده سازی فایل اکسل
# -------------------------------
def init_excel():
    if not os.path.exists(FILE_NAME):
        users = pd.DataFrame(columns=["username", "password_hash", "created_at"])
        transactions = pd.DataFrame(columns=["username", "type", "amount", "description", "date_shamsi"])
        with pd.ExcelWriter(FILE_NAME) as writer:
            users.to_excel(writer, sheet_name="users", index=False)
            transactions.to_excel(writer, sheet_name="transactions", index=False)

# -------------------------------
# مدیریت کاربران
# -------------------------------
def register_user(username: str, password: str) -> {bool, str} :
    if not username or not password:
        return False, "نام کاربری و رمز عبور نباید خالی باشند"
    xls = pd.ExcelFile(FILE_NAME)
    users = pd.read_excel(xls, sheet_name="users")
    if username in users["username"].values:
        return False, "این نام کاربری از قبل وجود دارد"
    pw_hash = hash_password(password)
    created_at = datetime.now().isoformat(timespec="seconds")
    new_user = pd.DataFrame([[username, pw_hash, created_at]], columns=["username", "password_hash", "created_at"])
    users = pd.concat([users, new_user], ignore_index=True)
    with pd.ExcelWriter(FILE_NAME, mode="a", if_sheet_exists="replace") as writer:
        users.to_excel(writer, sheet_name="users", index=False)
    return True, ""

def validate_user(username: str, password: str) -> bool:
    xls = pd.ExcelFile(FILE_NAME)
    users = pd.read_excel(xls, sheet_name="users")
    pw_hash = hash_password(password)
    result = users[(users["username"] == username) & (users["password_hash"] == pw_hash)]
    return not result.empty

# -------------------------------
# ذخیره تراکنش
# -------------------------------
def save_transaction(username: str, trans_type: str, amount: float, description: str, date_shamsi: str):
    xls = pd.ExcelFile(FILE_NAME)
    transactions = pd.read_excel(xls, sheet_name="transactions")
    new_data = pd.DataFrame([[username, trans_type, amount, description, date_shamsi]],
                            columns=["username", "type", "amount", "description", "date_shamsi"])
    transactions = pd.concat([transactions, new_data], ignore_index=True)
    with pd.ExcelWriter(FILE_NAME, mode="a", if_sheet_exists="replace") as writer:
        transactions.to_excel(writer, sheet_name="transactions", index=False)

# -------------------------------
# حذف تراکنش خاص
# -------------------------------
def delete_transaction(username, date_shamsi, description=None):
    xls = pd.ExcelFile(FILE_NAME)
    transactions = pd.read_excel(xls, sheet_name="transactions")
    condition = (transactions["username"] == username) & (transactions["date_shamsi"] == date_shamsi)
    if description:
        condition &= (transactions["description"] == description)
    if not transactions[condition].empty:
        transactions = transactions[~condition]
        with pd.ExcelWriter(FILE_NAME, mode="a", if_sheet_exists="replace") as writer:
            transactions.to_excel(writer, sheet_name="transactions", index=False)
        messagebox.showinfo("موفق", "تراکنش حذف شد")
    else:
        messagebox.showwarning("هشدار", "تراکنشی با مشخصات وارد شده یافت نشد")

# -------------------------------
# حذف حساب کاربری
# -------------------------------
def delete_user(username_to_delete):
    xls = pd.ExcelFile(FILE_NAME)
    users = pd.read_excel(xls, sheet_name="users")
    transactions = pd.read_excel(xls, sheet_name="transactions")
    if username_to_delete not in users["username"].values:
        messagebox.showwarning("هشدار", "این کاربر وجود ندارد")
        return
    confirm = messagebox.askyesno("تایید", f"آیا از حذف کاربر {username_to_delete} و تمام تراکنش‌هایش مطمئن هستید؟")
    if not confirm:
        return
    users = users[users["username"] != username_to_delete]
    transactions = transactions[transactions["username"] != username_to_delete]
    with pd.ExcelWriter(FILE_NAME, mode="a", if_sheet_exists="replace") as writer:
        users.to_excel(writer, sheet_name="users", index=False)
        transactions.to_excel(writer, sheet_name="transactions", index=False)
    messagebox.showinfo("موفق", f"کاربر {username_to_delete} و تمام تراکنش‌هایش حذف شدند")

# -------------------------------
# نمایش تمام تراکنش‌ها
# -------------------------------
def show_all_transactions():
    xls = pd.ExcelFile(FILE_NAME)
    transactions = pd.read_excel(xls, sheet_name="transactions")
    if transactions.empty:
        messagebox.showinfo("اطلاع", "هیچ تراکنشی ثبت نشده است")
        return
    win = tk.Toplevel()
    win.title("تمام تراکنش‌ها")
    win.geometry("900x500")
    win.resizable(True, True)
    frame = tk.Frame(win)
    frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(frame, columns=("username","type","amount","description","date_shamsi"), show="headings")
    tree.heading("username", text="کاربر")
    tree.heading("type", text="نوع تراکنش")
    tree.heading("amount", text="مبلغ")
    tree.heading("description", text="توضیح")
    tree.heading("date_shamsi", text="تاریخ (dd-mm-yyyy)")
    tree.column("username", width=120, anchor="center")
    tree.column("type", width=100, anchor="center")
    tree.column("amount", width=120, anchor="center")
    tree.column("description", width=300, anchor="w")
    tree.column("date_shamsi", width=150, anchor="center")
    vsb = tk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = tk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)
    for _, row in transactions.iterrows():
        tree.insert("", "end", values=(row["username"], row["type"], f"{row['amount']:,.0f}", row["description"], row["date_shamsi"]))

# -------------------------------
# الگوریتم تسویه حساب دو شریک
# -------------------------------
def partner_settlement(transactions, month):
    df_filtered = transactions[transactions["date_shamsi"].str.endswith(month)]
    if df_filtered.empty:
        return "هیچ تراکنشی برای این ماه وجود ندارد"
    all_users = df_filtered["username"].unique()
    income = df_filtered[df_filtered["type"]=="درآمد"].groupby("username")["amount"].sum()
    expense = df_filtered[df_filtered["type"]=="خرج"].groupby("username")["amount"].sum()
    total_income = income.sum() if not income.empty else 0
    total_expense = expense.sum() if not expense.empty else 0
    net_profit = total_income - total_expense
    equal_share = net_profit / len(all_users)
    result_text = f"📊 گزارش تسویه حساب ماه {month}\nمجموع درآمد: {total_income:,.0f} تومان\nمجموع خرج: {total_expense:,.0f} تومان\nسود نهایی: {net_profit:,.0f} تومان\nسهم هر شریک: {equal_share:,.0f} تومان\n\n"
    for user in all_users:
        user_income = income.get(user,0)
        user_expense = expense.get(user,0)
        user_real = user_income - user_expense
        diff = equal_share - user_real
        if diff > 0:
            result_text += f"{user} باید {diff:,.0f} تومان دریافت کند.\n"
        elif diff < 0:
            result_text += f"{user} باید {abs(diff):,.0f} تومان پرداخت کند.\n"
        else:
            result_text += f"{user} دقیقا سهم خود را دریافت کرده است.\n"
    return result_text

# -------------------------------
# گزارش ماهانه با اسکرول
# -------------------------------
def monthly_report():
    xls = pd.ExcelFile(FILE_NAME)
    transactions = pd.read_excel(xls, sheet_name="transactions")
    if transactions.empty:
        messagebox.showinfo("گزارش", "هیچ تراکنشی ثبت نشده است")
        return
    win = tk.Toplevel()
    win.title("گزارش آخر ماه")
    win.geometry("900x500")
    win.resizable(True, True)
    tk.Label(win, text="ماه مورد نظر (مثال: 07-1404)").pack(pady=(10, 5))
    entry_month = tk.Entry(win)
    entry_month.pack()
    frame = tk.Frame(win)
    frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(frame, columns=("user","income","expense","real","share","diff"), show="headings")
    tree.heading("user", text="کاربر")
    tree.heading("income", text="درآمد")
    tree.heading("expense", text="خرج")
    tree.heading("real", text="واقعی")
    tree.heading("share", text="سهم الگوریتم")
    tree.heading("diff", text="تفاوت")
    vsb = tk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = tk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)
    def generate_report():
        month = entry_month.get().strip()
        if not month:
            messagebox.showerror("خطا", "ماه را وارد کنید")
            return
        df_filtered = transactions[transactions["date_shamsi"].str.endswith(month)]
        if df_filtered.empty:
            messagebox.showinfo("گزارش", "تراکنشی برای این ماه یافت نشد")
            return
        all_users = df_filtered["username"].unique()
        income = df_filtered[df_filtered["type"]=="درآمد"].groupby("username")["amount"].sum()
        expense = df_filtered[df_filtered["type"]=="خرج"].groupby("username")["amount"].sum()
        total_income = income.sum() if not income.empty else 0
        total_expense = expense.sum() if not expense.empty else 0
        net_profit = total_income - total_expense
        equal_share = net_profit / len(all_users)
        for i in tree.get_children():
            tree.delete(i)
        for user in all_users:
            inc = income.get(user,0)
            exp = expense.get(user,0)
            real = inc - exp
            diff = equal_share - real
            tree.insert("", "end", values=(user, f"{inc:,.0f}", f"{exp:,.0f}", f"{real:,.0f}", f"{equal_share:,.0f}", f"{diff:,.0f}"))
    tk.Button(win, text="ساخت گزارش", command=generate_report).pack(pady=10)

# -------------------------------
# صفحه ورود
# -------------------------------
def login_screen():
    root = tk.Tk()
    root.title("ورود به سیستم")
    root.geometry("320x220")
    root.resizable(False, False)
    tk.Label(root, text="نام کاربری").pack(pady=(10, 0))
    entry_user = tk.Entry(root)
    entry_user.pack()
    tk.Label(root, text="رمز عبور").pack(pady=(8, 0))
    entry_pass = tk.Entry(root, show="*")
    entry_pass.pack()
    def try_login():
        user = entry_user.get().strip()
        pw = entry_pass.get().strip()
        if validate_user(user, pw):
            messagebox.showinfo("موفق", "ورود موفقیت‌آمیز بود")
            root.destroy()
            main_app(user)
        else:
            messagebox.showerror("خطا", "نام کاربری یا رمز عبور اشتباه است")
    def open_register_window():
        reg = tk.Toplevel(root)
        reg.title("ثبت نام")
        reg.geometry("340x260")
        reg.resizable(False, False)
        tk.Label(reg, text="نام کاربری").pack(pady=(10, 0))
        e_user = tk.Entry(reg)
        e_user.pack()
        tk.Label(reg, text="رمز عبور").pack(pady=(8, 0))
        e_pw = tk.Entry(reg, show="*")
        e_pw.pack()
        tk.Label(reg, text="تکرار رمز عبور").pack(pady=(8, 0))
        e_pw2 = tk.Entry(reg, show="*")
        e_pw2.pack()
        def do_register():
            u = e_user.get().strip()
            p1 = e_pw.get().strip()
            p2 = e_pw2.get().strip()
            if p1 != p2:
                messagebox.showerror("خطا", "رمزها با هم مطابقت ندارند")
                return
            success, msg = register_user(u, p1)
            if success:
                messagebox.showinfo("موفق", "ثبت نام انجام شد. حالا وارد شوید.")
                reg.destroy()
            else:
                messagebox.showerror("خطا", msg)
        tk.Button(reg, text="ثبت نام", command=do_register).pack(pady=12)
        tk.Button(reg, text="انصراف", command=reg.destroy).pack()
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=12)
    tk.Button(btn_frame, text="ورود", width=10, command=try_login).grid(row=0, column=0, padx=6)
    tk.Button(btn_frame, text="ثبت نام", width=10, command=open_register_window).grid(row=0, column=1, padx=6)
    tk.Button(root, text="خروج", width=22, command=root.destroy).pack(pady=(6, 0))
    root.mainloop()

# -------------------------------
# صفحه اصلی برنامه
# -------------------------------
def main_app(username: str):
    win = tk.Tk()
    win.title(f"برنامه مالی - {username}")
    win.geometry("450x600")
    win.resizable(True, True)
    tk.Label(win, text=f"خوش آمدی، {username}").pack(pady=(10, 6))
    tk.Label(win, text="نوع تراکنش").pack(pady=(6, 0))
    trans_type_var = tk.StringVar(value="درآمد")
    tk.Radiobutton(win, text="درآمد", variable=trans_type_var, value="درآمد").pack()
    tk.Radiobutton(win, text="خرج", variable=trans_type_var, value="خرج").pack()
    tk.Label(win, text="مبلغ").pack()
    entry_amount = tk.Entry(win)
    entry_amount.pack()
    tk.Label(win, text="توضیح").pack(pady=(6, 0))
    entry_desc = tk.Entry(win, width=50)
    entry_desc.pack()
    tk.Label(win, text="تاریخ (شمسی dd-mm-yyyy)").pack(pady=(6, 0))
    entry_date = tk.Entry(win)
    entry_date.insert(0, "مثال: 05-07-1404")
    entry_date.pack()
    # بخش حذف تراکنش
    tk.Label(win, text="برای حذف تراکنش، تاریخ و توضیح را وارد کنید").pack(pady=(10, 0))
    entry_del_date = tk.Entry(win)
    entry_del_date.insert(0, "مثال: 05-07-1404")
    entry_del_date.pack()
    entry_del_desc = tk.Entry(win)
    entry_del_desc.insert(0, "توضیح تراکنش")
    entry_del_desc.pack()
    # بخش حذف کاربر
    tk.Label(win, text="برای حذف یک کاربر، نام کاربری را وارد کنید").pack(pady=(10, 0))
    entry_del_user = tk.Entry(win)
    entry_del_user.pack()
    def save_data():
        try:
            amount = float(entry_amount.get())
            desc = entry_desc.get().strip()
            date_shamsi = entry_date.get().strip()
            t_type = trans_type_var.get()
            if not date_shamsi:
                messagebox.showerror("خطا", "تاریخ الزامی است")
                return
            # بررسی فرمت تاریخ: dd-mm-yyyy
            try:
                day, month, year = map(int, date_shamsi.split('-'))
                if not (1 <= day <= 31 and 1 <= month <= 12 and year > 1000):
                    raise ValueError
            except:
                messagebox.showerror("خطا", "فرمت تاریخ باید به صورت روز-ماه-سال (مثال: 05-07-1404) باشد")
                return
            save_transaction(username, t_type, amount, desc, date_shamsi)
            messagebox.showinfo("موفق", "تراکنش ذخیره شد")
            entry_amount.delete(0, tk.END)
            entry_desc.delete(0, tk.END)
            entry_date.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("خطا", "مبلغ باید عددی معتبر باشد")
    def delete_data():
        d_date = entry_del_date.get().strip()
        d_desc = entry_del_desc.get().strip()
        delete_transaction(username, d_date, d_desc)
    def delete_user_gui():
        user_to_del = entry_del_user.get().strip()
        if not user_to_del:
            messagebox.showerror("خطا", "نام کاربری الزامی است")
            return
        delete_user(user_to_del)
    tk.Button(win, text="ذخیره تراکنش", width=20, command=save_data).pack(pady=(6, 3))
    tk.Button(win, text="حذف تراکنش", width=20, command=delete_data).pack(pady=(3, 3))
    tk.Button(win, text="حذف کاربر", width=20, command=delete_user_gui).pack(pady=(3, 3))
    tk.Button(win, text="نمایش تمام تراکنش‌ها", width=25, command=show_all_transactions).pack(pady=(3, 3))
    tk.Button(win, text="📊 گزارش آخر ماه", width=20, command=monthly_report).pack(pady=(3, 3))
    tk.Button(win, text="خروج", width=20, command=win.destroy).pack(pady=(6, 0))
    win.mainloop()

# -------------------------------
# اجرای برنامه
# -------------------------------
if __name__ == "__main__":
    init_excel()
    login_screen()
