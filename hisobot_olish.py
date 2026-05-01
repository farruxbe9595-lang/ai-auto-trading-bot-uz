from saqlash.baza import bazani_tayyorla
from hisobotlar.hisobot_yaratish import oylik_hisobot_yarat

if __name__ == '__main__':
    bazani_tayyorla()
    path = oylik_hisobot_yarat()
    print('Hisobot yaratildi:', path)
