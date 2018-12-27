from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from appdb import Category, Item, User, Base

engine = create_engine('sqlite:///app.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

User1 = User(name="Robo Barista",
             email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')  # NOQA
session.add(User1)
session.commit()

cat1 = Category(name="samsung", user_id=1)
session.add(cat1)
session.commit()

item1 = Item(name="Galaxy S9",
             description="Low light photos ,Super Slow-mo, AR Emoji",
             category=cat1, user_id=1)
session.add(item1)
session.commit()

item2 = Item(name="Galaxy S8",
             description="Best Viewing Experience ,Enhanced Image Processing, Unlock Your Phone With A Glance",  # NOQA
             category=cat1, user_id=1)
session.add(item2)
session.commit()


cat2 = Category(name="apple", user_id=1)
session.add(cat2)
session.commit()

item1 = Item(name="iPhone XR",
             description="The largest LCD ever on an iPhone, Industry-leading color accuracy, Wide color gamut, Tap to wake",  # NOQA
             category=cat2, user_id=1)
session.add(item1)
session.commit()

item2 = Item(name="iPhone XS",
             description=" Super Retina HD display1,wide-angle and telephoto cameras",  # NOQA
             category=cat2, user_id=1)
session.add(item2)
session.commit()


cat3 = Category(name="Hwawei", user_id=1)
session.add(cat3)
session.commit()

item1 = Item(name="HUAWEI Mate 20",
             description="6.53'' 2244 x 1080 LCD display, 7nm Kirin 980 chipset, DUAL-NPU ,Leica Triple Camera, Leica Ultra Wide Angle Lens",  # NOQA
             category=cat3, user_id=1)
session.add(item1)
session.commit()

item2 = Item(name="HUAWEI Mate 20 Pro",
             description="6.39'' OLED 3120 x 1440 display, IP68, Kirin 980 chipset, 40W HUAWEI SuperCharge, Leica Triple Camera, In-screen Fingerprint, 3D Face Unlock",  # NOQA
             category=cat3, user_id=1)
session.add(item2)
session.commit()

print "added menu items!"
