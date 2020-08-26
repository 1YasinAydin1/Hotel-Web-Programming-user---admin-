from flask import (Flask, flash, logging, redirect, render_template, request,session, url_for)
import sqlite3 as sql
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
import datetime as dt
from functools import wraps
import os
import time
from bs4 import BeautifulSoup
import urllib
from urllib.request import urlopen
app = Flask(__name__)
app.secret_key="otel"
con=sql.connect("otel.db")
con.close()
# Kullanıcı Giriş Decarator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session: 
            return f(*args, **kwargs)
        else:
            return redirect(url_for("uye_giris"))
    return decorated_function
# kullanıcı kayıt formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min=4,max=25,message="4 ve 25 karakter arası giriş yapınız")])
    username = StringField("Kullanıcı adı",validators=[validators.Length(min=5,max=35,message="5 ve 35 karakter arası giriş yapınız")])
    email = StringField("E-mail",validators=[validators.Email(message="Lütfen Geçerli Bir E-mail adres giriniz")])
    password = PasswordField("Şifre",validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname="confirm",message="Parolanız uyuşmuyor")])
    confirm=PasswordField("Parola Doğrula")
# kullanıcı giriş formu
class LoginForm(Form):
    username = StringField("Kullanıcı adı") 
    password = PasswordField("Şifre") 
class AddForm(Form):
    name = StringField("Otel Ad ",validators=[validators.Length(min=4,max=25,message="4 ve 25 karakter arası giriş yapınız")])
    location = StringField("Otel Yer ",validators=[validators.Length(min=4,max=25,message="4 ve 25 karakter arası giriş yapınız")])
    star = StringField("Otel Yıldız ",validators=[validators.Length(min=4,max=25,message="4 ve 25 karakter arası giriş yapınız")])
    phone = StringField("Otel Tel ",validators=[validators.Length(min=4,max=25,message="4 ve 25 karakter arası giriş yapınız")])
@app.route("/")
def index():
    
    return render_template("index.html")
@app.route("/giris.html")
def giris_dondur():
    return render_template("giris.html")

# Üye kayıt işlemi
@app.route("/uye_kayit.html",methods=["GET","POST"])
def uye_kayit():
    form=RegisterForm(request.form)
    if request.method=="POST"  and form.validate():
        username = form.username.data 
        name=form.name.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)
        with sql.connect('otel.db') as con:
            cur=con.cursor()
            cur.execute("""SELECT * FROM uyeler WHERE uye_mail = '%s'"""%(email,))
            data=cur.fetchone()
            if data:
                flash("Bu e-mailde kayıtlı kullanıcı zaten var")
                return redirect(url_for("uye_kayit"))
            else:
                pass
            cur.execute("insert into uyeler(uye_adsoyad,uye_kulad,uye_mail,uye_sifre) values(?,?,?,?)",(name,username,email,password))
            con.commit()
        con.close()     
        return redirect(url_for("uye_giris"))
    else:
        return render_template("uye_kayit.html",form=form)
# Üye giriş işlemi
class Sepet:
        urunler={}
@app.route("/uye_giris.html",methods=["GET","POST"])
def uye_giris():
    form=LoginForm(request.form)
    if request.method=="POST":
        global username
        username=form.username.data
        password_entered=form.password.data
        with sql.connect('otel.db') as con:
            cur=con.cursor()
            cur.execute("""SELECT * FROM uyeler WHERE uye_kulad = '%s'"""%(username,))
            data=cur.fetchone()
            if data:
              real_password=data[3]
              if sha256_crypt.verify(password_entered,real_password):
                  session["logged_in"]=True
                  session["username"]=username
                  msg="Hoşgeldin "+data[0]+"!" 
                  global sepet
                  sepet=Sepet()
                  sepet.urunler[2]=data[4]
                  return render_template("index.html",msg=msg)
              else: 
                  flash("Parolayı yanlış girdiniz ")
            else:
                flash("Böyle bir kullanıcı adı yoktur")
                return redirect(url_for("uye_giris"))
                
    return render_template("uye_giris.html",form=form)
# Üye çıkış işlemi
@app.route("/logout")
@login_required
def logout():
    session.clear()
    global sepet
    sepet=Sepet()
    del sepet
    global sayac
    sayac=0
    return redirect(url_for("index"))


@app.route("/reservation")
@login_required
def reservation():
    with sql.connect('otel.db') as con:
                    
                    cur=con.cursor()
                    cur.execute("select * from rezervasyon WHERE rez_id = '%s'"%(13))
                    data = cur.fetchone()
                    if data:
                        rezdaid=data[2]
                        bastar=data[3]
                        bittar=data[4]

                        cur.execute("select * from odalar WHERE oda_id = '%s'"%(rezdaid))
                        data1 = cur.fetchone()
                        yataks=data1[0]
                        odano=data1[8]
                        otelid=data1[7]
                        odaucret=data1[5]

                        cur.execute("select * from otel WHERE otel_id = '%s'"%(otelid))
                        data2 = cur.fetchone()
                        otead=data2[0]
                        return render_template("reservation.html",msg=otead,msg1=yataks,msg2=odano,msg3=odaucret,msg4=bastar,msg5=bittar)
                    else:
                        msg="Henüz rezervasayon yapmadınız"
                        return render_template("reservation.html",mesaj=msg)
class oteller:
        otelad={}
sayac=0
@app.route("/basket",methods=['POST','GET'])
@login_required
def basket():
    
    basstr=request.form['tarihbaslangıc']
    # basdate= dt.strptime(basstr,"%m/%d/%Y")
    
    bitisstr=request.form['tarihbitis']
     #bitisdate= dt.strptime(bitisstr,"%m/%d/%Y")
    if session["logged_in"]:
        global sepet
        global sayac
        sepet=Sepet()
        
        sepet.urunler[0]=basstr
        sepet.urunler[1]=bitisstr
        
        sayac=sayac+1
        global n1
        n1=dt.datetime.now()
    else:
        return redirect(url_for("uye_giris"))
    return render_template("index.html",sayac=sayac)

@app.route("/sil",methods=['POST','GET'])
@login_required
def sil():
    global sepet
    sepet=Sepet()
    del sepet
    mesaj="Sepetiniz Boştur"
    global sayac
    sayac=0
    return render_template("basketlist.html",mesaj=mesaj)
@app.route("/Yap",methods=['POST','GET'])
@login_required
def Yap():
    global sepet
    global sayac
    sepet=Sepet()
   
    with sql.connect('otel.db') as con:
            cur=con.cursor()
            cur.execute("insert into rezervasyon(foruye_id,rezoda_id,oda_rez_bas,oda_rez_bitis) values(?,?,?,?)",(2,1,sepet.urunler[0],sepet.urunler[1]))
            con.commit()
    con.close() 
    del sepet
    sayac=0
    return render_template("index.html")    

s="58"   
a=dt.datetime.strptime(s,"%S")
b=dt.datetime.strftime(a,"%S") 


@app.route('/basketlist.html')
def basketlist():
    global sepet
    sepet=Sepet()
    global sayac
   
  
    if sayac==0 :
        msg="Sepetiniz Boştur"
        return render_template("basketlist.html",mesaj=msg)
    else:
        
        url = "http://127.0.0.1:5000/odalar.html"
        sayfa = urllib.request.urlopen(url)
        soup = BeautifulSoup(sayfa, "html.parser")
        ana = soup.find('div')
        alt=ana.findAll('h3',attrs={"class":"card-title"})    
        sayac=alt[0].text
        with sql.connect('otel.db') as con:
            cur=con.cursor()
            cur.execute("select * from otel WHERE otel_id  = '%s'"%(sayac))
            
            data = cur.fetchone()
            otel_adi=data[0]
            otel_adresi=data[1]
            otel_yildizi=data[2]
            otel_id=data[4]

            cur.execute("select * from odalar WHERE forotel_id = '%s'"%(otel_id))
            data00 = cur.fetchone()
            otel_yataksayisi=data00[0]
            otel_artilar1=data00[2]
            otel_artilar2=data00[3]
            otel_artilar3=data00[4]
            otel_ucret=data00[5] 
            odaid=data00[6] 

              
        return render_template("basketlist.html",msg=otel_adi,msg1=otel_adresi,msg2=otel_yildizi,msg3=otel_yataksayisi,msg4=otel_artilar1,msg5=otel_artilar2,msg6=otel_artilar3,msg7=otel_ucret)
    
@app.route("/admin.html")
def admin():
    return redirect(url_for("admin"))

@app.route('/ekle.html')
def ekle():
   return render_template("ekle.html")
   
@app.route('/sil.html')
def sisil():
   return render_template("sil.html")
@app.route('/guncelle.html')
def guncelle():
   return render_template("guncelle.html")
@app.route('/eeekle',methods=['POST','GET'])
def eeekle():
    if request.method=='POST':
   
            otelad=request.form['otelad']
            otelyer=request.form['otelyer']
            otelyildiz=request.form['otelyildiz']
            oteltel=request.form['oteltel']
            oda_ytk=request.form['oda_ytk']
            oda_kat=request.form['oda_kat']
            oda_ekt1=request.form['oda_ekt1']
            oda_ekt2=request.form['oda_ekt2']
            oda_ekt3=request.form['oda_ekt3']
            oda_ucrt=request.form['oda_ucrt']
            oda_no=request.form['oda_no']
            
            with sql.connect('otel.db') as con:  
                cur=con.cursor()
                cur.execute("select otel_id from otel WHERE otel_ad = ?",(otelad))
                data = cur.fetchone()
                otel__iid=data[0]

                cur.execute("""INSERT INTO otel(otel_ad,otel_yer,otel_yildiz,otel_tel) VALUES (?,?,?,?)""",(otelad,otelyer,otelyildiz,oteltel))
                cur.execute("""INSERT INTO odalar(oda_yataks,oda_kat,oda_ozel1,oda_ozel2,oda_ozel3,oda_ucret,oda_no,forotel_id)
                 VALUES (?,?,?,?,?,?,?,?)""",(oda_ytk,oda_kat,oda_ekt1,oda_ekt2,oda_ekt3,oda_ucrt,oda_no,otel__iid))
                con.commit()
            con.close()   
            msg="başarılı"
  
            return render_template("ekle.html",msg=msg)
otelaad=""
@app.route('/gunc_on_adim',methods=['POST','GET'])
def gunc_on_adim():
    otelad=request.form['otelad']
    global otelaad
    otelaad=otelad
    if request.method=='POST':
        with sql.connect('otel.db') as con:  
                cur=con.cursor()
                cur.execute("select otel_id from otel WHERE otel_ad= '%s'"%(otelad))
                data = cur.fetchone()
                if data:
                    msg=" "
                else:
                    msg="Böyle bir Otel mevcut değil"
        return render_template("guncelle.html",msg=msg)
  
@app.route('/gunc',methods=['POST','GET'])
def gunc():
    if request.method=='POST':
   
            otelad=request.form['otelad']
            otelyer=request.form['otelyer']
            otelyildiz=request.form['otelyildiz']
            oteltel=request.form['oteltel']
            oda_ytk=request.form['oda_ytk']
            oda_kat=request.form['oda_kat']
            oda_ekt1=request.form['oda_ekt1']
            oda_ekt2=request.form['oda_ekt2']
            oda_ekt3=request.form['oda_ekt3']
            oda_ucrt=request.form['oda_ucrt']
            oda_no=request.form['oda_no']
            global otelaad
            with sql.connect('otel.db') as con:  
                cur=con.cursor()
                cur.execute("select otel_id from otel WHERE otel_ad = '%s'"%(otelaad))
                data = cur.fetchone()
                otel__id=data[0]

                cur.execute("UPDATE otel SET otel_ad=?,otel_yer=?,otel_yildiz=?,otel_tel=? WHERE otel_id=?",(otelad,otelyer,otelyildiz,oteltel,otel__id))
                cur.execute("UPDATE odalar SET oda_yataks=?,oda_kat=?,oda_ozel1=?,oda_ozel2=?,oda_ozel3=?,oda_ucret=?,oda_no=? WHERE forotel_id=?",(oda_ytk,oda_kat,oda_ekt1,oda_ekt2,oda_ekt3,oda_ucrt,oda_no,otel__id))
                con.commit()
            con.close()   
            msg="başarılı"
  
            return render_template("admin.html",msg=msg)
@app.route('/siil',methods=['POST','GET'])
def siil():
    
    if request.method=='POST':
        try:
            otelad=request.form['otelad']
            with sql.connect('otel.db') as con:
                msg="s"
                cur=con.cursor()
                cur.execute("DELETE FROM otel WHERE otel_ad='%s'"%(otelad))
            con.commit()    
            msg="başarılı"
        except:
            msg="başarısız"
        finally:
            con.close()   
            return render_template("sil.html",msg=msg)
@app.route('/admin_giris',methods=['POST','GET'])
def admin_giris():
     
    if request.method=='POST':
        try:
            admnk_ad=request.form['admnad']
            admnk_sifre=request.form['admnsifre']
            with sql.connect('otel.db') as con:  
                cur=con.cursor()
                cur.execute("""SELECT * FROM admin WHERE kulad_admn = '%s' AND sifre_admn = '%s'"""%(admnk_ad,admnk_sifre))
                data=cur.fetchone()
                if data:
                    msg="Hoşgeldin {}".format(data[0])
                else:
                    msg="Yanlış giriş!"
        except:
            msg="başarısız"
        finally:
            con.close()
            if msg=="Yanlış giriş!":
                return render_template("giris.html",msg=msg) 
            else:   
                return render_template("admin.html",msg=msg)
            
@app.route("/hakkimizda.html")
def hakkimizda():
     return render_template("hakkimizda.html")

@app.route("/odalar.html")
def odalar():
    try:
        with sql.connect('otel.db') as con:

                    global otel_ad
                    otel_ad=oteller()

                    
                    cur=con.cursor()
                    cur.execute("select * from otel WHERE otel_id = '%s'"%(1))
                    data = cur.fetchone()
                    otels1=data[0]
                    otelid1=data[4]
                    otel2=data[1]
                    otel3=data[2]

                    cur.execute("select * from odalar WHERE forotel_id = '%s'"%(1))
                    data00 = cur.fetchone()
                    otel110=data00[0]
                    otel111=data00[2]
                    otel112=data00[3]
                    otel113=data00[4]
                    otel114=data00[5]
                    otel115=data00[6]



                    cur.execute("select * from otel WHERE otel_id = '%s'"%(2)) 
                    data1 = cur.fetchone()
                    otel5=data1[0]
                    otelid2=data1[4]
                    otel6=data1[1]
                    otel7=data1[2]

                    cur.execute("select * from odalar WHERE forotel_id = '%s'"%(2))
                    data01 = cur.fetchone()
                    otel220=data01[0]
                    otel221=data01[2]
                    otel222=data01[3]
                    otel223=data01[4]
                    otel224=data01[5]
                    otel225=data01[6]



                    cur.execute("select * from otel WHERE otel_id = '%s'"%(3)) 
                    data2 = cur.fetchone()
                    otel9=data2[0]
                    otelid3=data2[4]
                    otel10=data2[1]
                    otel11=data2[2]

                    cur.execute("select * from odalar WHERE forotel_id = '%s'"%(3))
                    data02 = cur.fetchone()
                    otel330=data02[0]
                    otel331=data02[2]
                    otel332=data02[3]
                    otel333=data02[4]
                    otel334=data02[5]
                    otel335=data02[6]



                    cur.execute("select * from otel WHERE otel_id = '%s'"%(4)) 
                    data3 = cur.fetchone()
                    otel13=data3[0]
                    otelid4=data3[4]
                    otel14=data3[1]
                    otel15=data3[2]

                    cur.execute("select * from odalar WHERE forotel_id = '%s'"%(4))
                    data03 = cur.fetchone()
                    otel440=data03[0]
                    otel441=data03[2]
                    otel442=data03[3]
                    otel443=data03[4]
                    otel444=data03[5]
                    otel445=data03[6]



                    cur.execute("select * from otel WHERE otel_id = '%s'"%(5)) 
                    data4 = cur.fetchone()
                    otel17=data4[0]
                    otelid5=data4[4]
                    otel18=data4[1]
                    otel19=data4[2]

                    cur.execute("select * from odalar WHERE forotel_id = '%s'"%(5))
                    data04 = cur.fetchone()
                    otel550=data04[0]
                    otel551=data04[2]
                    otel552=data04[3]
                    otel553=data04[4]
                    otel554=data04[5]
                    otel555=data04[6]



                    cur.execute("select * from otel WHERE otel_id = '%s'"%(6)) 
                    data5 = cur.fetchone()
                    otel21=data5[0]
                    otelid6=data5[4]
                    otel22=data5[1]
                    otel23=data5[2]

                    cur.execute("select * from odalar WHERE forotel_id = '%s'"%(6))
                    data05 = cur.fetchone()
                    otel660=data05[0]
                    otel661=data05[2]
                    otel662=data05[3]
                    otel663=data05[4]
                    otel664=data05[5]
                    otel665=data05[6]



                    cur.execute("select * from otel WHERE otel_id = '%s'"%(7)) 
                    data6 = cur.fetchone()
                    otel25=data6[0]
                    otelid7=data6[4]
                    otel26=data6[1]
                    otel27=data6[2]
                    
                    cur.execute("select * from odalar WHERE forotel_id = '%s'"%(7))
                    data06 = cur.fetchone()
                    otel770=data06[0]
                    otel771=data06[2]
                    otel772=data06[3]
                    otel773=data06[4]
                    otel774=data06[5]
                    otel775=data06[6]



                    cur.execute("select * from otel WHERE otel_id = '%s'"%(8)) 
                    data7 = cur.fetchone()
                    otel29=data7[0]
                    otelid8=data7[4]
                    otel30=data7[1]
                    otel31=data7[2]
                    
                    cur.execute("select * from odalar WHERE forotel_id = '%s'"%(8))
                    data07 = cur.fetchone()
                    otel880=data07[0]
                    otel881=data07[2]
                    otel882=data07[3]
                    otel883=data07[4]
                    otel884=data07[5]
                    otel885=data07[6]



                    cur.execute("select * from otel WHERE otel_id = '%s'"%(9)) 
                    data8= cur.fetchone()
                    otel33=data8[0]
                    otelid9=data8[4]
                    otel34=data8[1]
                    otel35=data8[2]
                    
                    cur.execute("select * from odalar WHERE forotel_id = '%s'"%(9))
                    data08 = cur.fetchone()
                    otel990=data08[0]
                    otel991=data08[2]
                    otel992=data08[3]
                    otel993=data08[4]
                    otel994=data08[5]
                    otel995=data08[6]


    except:             
            msg="Yükleme Başarısız oldu"
    finally:
            con.close()
            return render_template("odalar.html",msg=otels1,msg2=otel2,msg3=otel3,msg110=otel110,msg111=otel111,msg112=otel112,msg113=otel113,msg114=otel114,msg115=otel115
                                                ,msg5=otel5,msg6=otel6,msg7=otel7,msg220=otel220,msg221=otel221,msg222=otel222,msg223=otel223,msg224=otel224,msg225=otel225
                                                ,msg9=otel9,msg10=otel10,msg11=otel11,msg330=otel330,msg331=otel331,msg332=otel332,msg333=otel333,msg334=otel334,msg335=otel335
                                                ,msg13=otel13,msg14=otel14,msg15=otel15,msg440=otel440,msg441=otel441,msg442=otel442,msg443=otel443,msg444=otel444,msg445=otel445
                                                ,msg17=otel17,msg18=otel18,msg19=otel19,msg550=otel550,msg551=otel551,msg552=otel552,msg553=otel553,msg554=otel554,msg555=otel555
                                                ,msg21=otel21,msg22=otel22,msg23=otel23,msg660=otel660,msg661=otel661,msg662=otel662,msg663=otel663,msg664=otel664,msg665=otel665
                                                ,msg25=otel25,msg26=otel26,msg27=otel27,msg770=otel770,msg771=otel771,msg772=otel772,msg773=otel773,msg774=otel774,msg775=otel775
                                                ,msg29=otel29,msg30=otel30,msg31=otel31,msg880=otel880,msg881=otel881,msg882=otel882,msg883=otel883,msg884=otel884,msg885=otel885
                                                ,msg33=otel33,msg34=otel34,msg35=otel35,msg990=otel990,msg991=otel991,msg992=otel992,msg993=otel993,msg994=otel994,msg995=otel995
                                                ,otelid1=otelid1,otelid2=otelid2,otelid3=otelid3,otelid4=otelid4,otelid5=otelid5,otelid6=otelid6,otelid7=otelid7,otelid8=otelid8,otelid9=otelid9)            


if __name__=="__main__":
    app.run(debug=True)

