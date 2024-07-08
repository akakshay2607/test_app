from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.screenmanager import ScreenManager
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.button import MDFlatButton,MDRaisedButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList,OneLineListItem
from kiteconnect import KiteTicker
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.snackbar import Snackbar
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition, SwapTransition
from kiteconnect import KiteConnect
import pandas as pd
import webbrowser

class stocks_app:
    def __init__(self,new_session=False):
        self.kite = KiteConnect(api_key="j8xt637urobqdrtb")
        self.logged_in = False
        try:
            if new_session:
                with open('request_token.txt') as f:
                    text = f.readlines()
                token = text[0]
                data = self.kite.generate_session(token, api_secret="56morn12cti706aw344ytibwbscyoaba")
                self.kite.set_access_token(data["access_token"])
                with open('access_token.txt','w') as f:
                    f.writelines(data["access_token"])
            else:
                with open('access_token.txt') as f:
                    text = f.readlines()
                access_token = text[0]
                self.kite.set_access_token(access_token)
            self.profile = self.kite.profile()
            self.get_instruments()
            self.logged_in = True
        except:
            self.logged_in = False
            pass
        
    def get_instruments(self):
        self.instruments = self.kite.instruments()
        self.instr_df = pd.DataFrame(self.instruments)

    def get_last_price(self,index):
        if index == 'BANKNIFTY':
            sym = 'NSE:NIFTY BANK'
        elif index == 'FINNIFTY':
            sym = 'NSE:NIFTY FIN SERVICE'
        elif index == 'NIFTY':
            sym = 'NSE:NIFTY 50'
        return self.kite.quote(sym)[sym]['last_price']

    def get_strike_prices(self,index,instr_type):
        lp = self.get_last_price(index)
        df = self.instr_df[(self.instr_df['name'] == index) & (self.instr_df['instrument_type'] == instr_type)].sort_values(by=['expiry'],ascending=True)
        df = df[df.expiry==df['expiry'].values[0]]
        sp = round(lp/50)*50
        sp1 = round(lp/100)*100
        df = df.sort_values(by=['strike']).reset_index(drop=True)
        try:
            sp_idx = df[df.strike == sp].index[0]
        except:
            sp_idx = df[df.strike == sp1].index[0]
        idxes = [i for i in range(sp_idx-5,sp_idx)]
        idxes.extend([i for i in range(sp_idx+1,sp_idx+6)])
        return df.iloc[idxes]
    
    def get_profile(self):
        profile = self.kite.profile()
        user = profile['user_name']
        em_ = profile['email']
        broker = profile['broker']
        return user,em_,broker
    
global ap
ap = stocks_app()

class Stocks(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(Builder.load_file('main1.kv'))
        self.screen_manager.add_widget(Builder.load_file('profile.kv'))
        self.screen_manager.add_widget(Builder.load_file('kiteLogin.kv'))
        return self.screen_manager
    
    def on_start(self):
        global ap
        if not ap.logged_in:
            self.open_login()
        else:
            self.screen_manager.current = 'Main'

    def authenticate_(self,token):
        global ap
        with open('request_token.txt','w') as f:
            f.writelines(token)
        ap = stocks_app(new_session=True)
        if ap.logged_in:
            self.screen_manager.current = 'Main'
        else:
            self.screen_manager.current = 'kite'

    def open_url(self, url):
        webbrowser.open(url)

    def open_login(self):
        self.screen_manager.current = 'kite'

    def open_menu(self):
        menu_items = [
            {
                "text": f"{i}",
                "viewclass": "OneLineListItem",
                "on_release": lambda x=f"{i}": self.menu_callback(x),
            } for i in ['NIFTY','FINNIFTY','BANKNIFTY']
        ]
        self.menu = MDDropdownMenu(caller=self.screen_manager.get_screen('Main').ids.index_button, items=menu_items,width_mult=3,)
        self.menu.open()

    def show_main(self):
        self.screen_manager.transition = SlideTransition(direction='right')
        self.screen_manager.current = 'Main'
        
    def show_profile(self):
        self.screen_manager.transition = SlideTransition(direction='left')
        self.screen_manager.current = 'Profile'
        pass
        
    def open_menu1(self):
        menu_items = [
            {
                "text": f"{i}",
                "viewclass": "OneLineListItem",
                "on_release": lambda x=f"{i}": self.menu_callback1(x),
            } for i in ['CE','PE']
        ]
        self.menu1 = MDDropdownMenu(caller=self.screen_manager.get_screen('Main').ids.instrument, items=menu_items,width_mult=3)
        self.menu1.open()

    def menu_callback(self, text_item):
        self.screen_manager.get_screen('Main').ids.index_button.text = text_item
        self.index = text_item.strip()
        self.menu.dismiss()
    
    def menu_callback1(self, text_item):
        global ap
        self.screen_manager.get_screen('Main').ids.instrument.text = text_item
        self.menu1.dismiss()
        self.instrument = text_item
        df = ap.get_strike_prices(self.index,self.instrument)
        symbl = list(df['tradingsymbol'])
        trd = list(df['strike'])
        self.list_view(symbl,trd)

    def list_view(self,symbl,strk):
        container = self.root.get_screen('Main').ids.list_container
        container.clear_widgets()
        scrl = MDScrollView(
        )
        list_ = MDList()
        scrl.add_widget(list_)
        for i in range(len(symbl)):
            item = OneLineListItem(text=f"{symbl[i]} -  {strk[i]}")
            item.bind(on_release=self.on_list_item_click)
            list_.add_widget(item)
        self.screen_manager.get_screen('Main').ids.list_container.add_widget(scrl)
    
    def on_list_item_click(self,i):
        self.dialog = MDDialog(
            title=i.text,
            type = 'custom',
            content_cls=MDGridLayout(
                MDTextField(
                    id='cd_high',
                    helper_text="Candle High",
                    size_hint_x=0.2,
                    helper_text_mode = "persistent",
                    required=True,
                ),
                MDTextField(
                    id='cd_low',
                    helper_text="Candle Low",
                    size_hint_x=0.2,
                    helper_text_mode = "persistent",
                    required=True,
                ),
                MDTextField(
                    id='t1',
                    helper_text="T1",
                    size_hint_x=0.2,
                    helper_text_mode = "persistent",
                    required=True,
                ),
                MDTextField(
                    id='retcr',
                    helper_text="Retracement Point",
                    size_hint_x=0.2,
                    helper_text_mode = "persistent",
                    required=True,
                ),
                MDTextField(
                    id='sl_pt',
                    helper_text="Daily SL",
                    size_hint_x=0.2,
                    helper_text_mode = "persistent",
                    required=True,
                ),
                MDTextField(
                    id='len_entry',
                    helper_text="Entry candle Max length",
                    size_hint_x=0.2,
                    helper_text_mode = "persistent",
                    required=True,
                ),
                MDTextField(
                    id='book_per',
                    helper_text="Booking %",
                    size_hint_x=0.2,
                    helper_text_mode = "persistent",
                    required=True,
                ),
                cols=2,
                spacing="12dp",
                size_hint_y=None,
                height="240dp",
            ),
            buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release = self.close_dialog
                    ),
                    MDRaisedButton(
                        text="OK",
                        # theme_text_color="Custom",
                        # text_color=self.theme_cls.primary_color,
                        on_release = self.open_confirmation
                    ),
                ],
        )
        self.dialog.open()  

    def close_dialog(self,*args):
        self.dialog.dismiss()

    def check_fields(self):
        required_fields = [
            self.dialog.content_cls.ids.cd_high,
            self.dialog.content_cls.ids.cd_low,
            self.dialog.content_cls.ids.t1,
            self.dialog.content_cls.ids.retcr,
            self.dialog.content_cls.ids.sl_pt,
            self.dialog.content_cls.ids.len_entry,
            self.dialog.content_cls.ids.book_per,
        ]
        empty_fields = [field for field in required_fields if not field.text]
        if empty_fields:
            for field in empty_fields:
                field.error = True
            Snackbar(text="Please fill all required fields.").open()
            return False
        return required_fields
    
    def place_order(self,*args):
        self.confirm_dia.dismiss()
        self.dialog.dismiss()
        Snackbar(
            text="Order placed!!",
            snackbar_x="10dp",
            snackbar_y="10dp",
            pos_hint = {'center_x':0.5,'center_y':0.9}
        ).open()

    def open_confirmation(self,*args):
        fields = self.check_fields()
        if fields:
            self.confirm_dia = MDDialog(
                title='Want to Place the order?',
                type = 'custom',
                buttons=[
                        MDFlatButton(
                            text="CANCEL",
                            theme_text_color="Custom",
                            text_color=self.theme_cls.primary_color,
                            on_release = self.close_confirm_dia
                        ),
                        MDRaisedButton(
                            text="Place order",
                            on_release = lambda x: (self.place_order(),self.close_confirm_dia())
                        ),
                    ],
            )
            self.confirm_dia.open()

    def close_confirm_dia(self,*args):
        self.confirm_dia.dismiss()

Stocks().run()


