import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import threading
import time

class StockTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Price Tracker | github.com/isthorius")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Variables
        self.stock_symbol = tk.StringVar(value="AAPL")
        self.refresh_interval = tk.IntVar(value=60)  # in seconds
        self.time_period = tk.StringVar(value="1d")
        self.tracking = False
        self.stock_data = None
        self.update_thread = None
        
        # Setup UI
        self.create_widgets()
        
        # Load initial data
        self.fetch_stock_data()
        
    def create_widgets(self):
        # Create main frames
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        data_frame = ttk.Frame(self.root, padding="10")
        data_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control Frame
        ttk.Label(control_frame, text="Stock Symbol:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(control_frame, textvariable=self.stock_symbol, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Time Period:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Combobox(control_frame, textvariable=self.time_period, values=["1d", "5d", "1mo", "3mo", "6mo", "1y"], width=5).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Refresh (sec):").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        ttk.Spinbox(control_frame, textvariable=self.refresh_interval, from_=10, to=3600, width=5).grid(row=0, column=5, padx=5, pady=5)
        
        self.track_button = ttk.Button(control_frame, text="Start Tracking", command=self.toggle_tracking)
        self.track_button.grid(row=0, column=6, padx=10, pady=5)
        
        ttk.Button(control_frame, text="Fetch Data", command=self.fetch_stock_data).grid(row=0, column=7, padx=5, pady=5)
        
        # Data Frame - Split into left (info) and right (chart)
        data_left = ttk.Frame(data_frame)
        data_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        data_right = ttk.Frame(data_frame)
        data_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Left Frame - Stock Info
        self.info_text = tk.Text(data_left, wrap=tk.WORD, height=10, font=('Consolas', 10))
        self.info_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Left Frame - History Table
        columns = ("Date", "Open", "High", "Low", "Close", "Volume")
        self.history_tree = ttk.Treeview(data_left, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=80, anchor=tk.CENTER)
        
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        
        # Right Frame - Chart
        self.figure, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=data_right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def fetch_stock_data(self):
        symbol = self.stock_symbol.get().upper()
        
        try:
            # Get stock data
            stock = yf.Ticker(symbol)
            
            # Get current price and info
            hist = stock.history(period="1d")
            if hist.empty:
                raise ValueError("No data found for this symbol")
                
            current_price = hist["Close"].iloc[-1]
            
            # Get historical data for selected period
            period = self.time_period.get()
            self.stock_data = stock.history(period=period)
            
            # Update info display
            self.update_info_display(stock, current_price)
            
            # Update history table
            self.update_history_table()
            
            # Update chart
            self.update_chart()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch data: {str(e)}")
    
    def update_info_display(self, stock, current_price):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        # Basic info
        info = stock.info
        display_text = f"Stock: {info.get('longName', 'N/A')} ({self.stock_symbol.get()})\n"
        display_text += f"Current Price: ${current_price:.2f}\n"
        
        # Market info
        display_text += f"Market Cap: ${info.get('marketCap', 'N/A'):,}\n"
        display_text += f"52 Week Range: ${info.get('fiftyTwoWeekLow', 'N/A')} - ${info.get('fiftyTwoWeekHigh', 'N/A')}\n"
        display_text += f"PE Ratio: {info.get('trailingPE', 'N/A')}\n"
        display_text += f"Dividend Yield: {info.get('dividendYield', 'N/A')*100 if info.get('dividendYield') else 'N/A'}%\n"
        
        # Price change info
        if len(self.stock_data) >= 2:
            prev_close = self.stock_data["Close"].iloc[-2]
            change = current_price - prev_close
            percent_change = (change / prev_close) * 100
            display_text += f"Change: {'+' if change >= 0 else ''}{change:.2f} ({'+' if percent_change >= 0 else ''}{percent_change:.2f}%)\n"
        
        self.info_text.insert(tk.END, display_text)
        self.info_text.config(state=tk.DISABLED)
    
    def update_history_table(self):
        # Clear existing data
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)
        
        # Add new data (show latest 20 entries)
        for index, row in self.stock_data.tail(20).iterrows():
            date_str = index.strftime('%Y-%m-%d')
            self.history_tree.insert("", tk.END, values=(
                date_str,
                f"{row['Open']:.2f}",
                f"{row['High']:.2f}",
                f"{row['Low']:.2f}",
                f"{row['Close']:.2f}",
                f"{row['Volume']:,}"
            ))
    
    def update_chart(self):
        self.ax.clear()
        
        if self.stock_data is not None and not self.stock_data.empty:
            # Convert index to DatetimeIndex if it's not already
            if not isinstance(self.stock_data.index, pd.DatetimeIndex):
                self.stock_data.index = pd.to_datetime(self.stock_data.index)
                
            # Plot the data
            self.stock_data['Close'].plot(ax=self.ax, title=f"{self.stock_symbol.get()} Stock Price", grid=True)
            self.ax.set_ylabel("Price ($)")
            self.ax.set_xlabel("Date")
            
            # Format x-axis for better date display
            if len(self.stock_data) > 10:  # For longer periods, show fewer labels
                self.ax.xaxis.set_major_locator(plt.MaxNLocator(6))
            
            self.figure.autofmt_xdate()
            self.canvas.draw()
    
    def toggle_tracking(self):
        if self.tracking:
            self.stop_tracking()
        else:
            self.start_tracking()
    
    def start_tracking(self):
        self.tracking = True
        self.track_button.config(text="Stop Tracking")
        self.update_thread = threading.Thread(target=self.tracking_loop, daemon=True)
        self.update_thread.start()
    
    def stop_tracking(self):
        self.tracking = False
        self.track_button.config(text="Start Tracking")
    
    def tracking_loop(self):
        while self.tracking:
            self.fetch_stock_data()
            time.sleep(self.refresh_interval.get())

if __name__ == "__main__":
    root = tk.Tk()
    app = StockTrackerApp(root)
    root.mainloop()
