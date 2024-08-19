from django.db import models


class CategoryProduct(models.Model):
    name = models.CharField(max_length=100)
    img = models.ImageField(upload_to="images/category/")

    def __str__(self):
        return self.name

class FAQ(models.Model):
    question = models.CharField(max_length=255, verbose_name="سوال")
    answer = models.TextField(verbose_name="پاسخ")
    def __str__(self):
        return self.question

class PhoneCompany(models.Model):
    phone = models.CharField(max_length=15, verbose_name='شماره تلفن')

    def __str__(self):
        return self.phone

class ImageCompany(models.Model):
    image = models.ImageField(upload_to="images/company/")


class Footer(models.Model):
    name = models.CharField(verbose_name='اسم شرکت',null=True , blank=True , max_length=100)
    description = models.TextField(verbose_name='توضیحات فوتر')
    address = models.TextField(verbose_name='آدرس شرکت')
    email = models.EmailField(verbose_name='ایمیل شرکت')
    phone = models.ManyToManyField(PhoneCompany, verbose_name='شماره‌های تلفن شرکت')
    img = models.ManyToManyField(ImageCompany,verbose_name='عکس های شرکت')
    instagram = models.URLField(verbose_name='آدرس اینستاگرام شرکت', null=True, blank=True)
    id_instagram = models.CharField(max_length=50, verbose_name='آیدی اینستاگرام شرکت', null=True, blank=True)

    telegram = models.URLField(verbose_name='آدرس تلگرام شرکت', null=True, blank=True)
    id_telegram = models.CharField(max_length=50, verbose_name='آیدی تلگرام شرکت', null=True, blank=True)

    eitaa = models.URLField(verbose_name='آدرس ایتا شرکت', null=True, blank=True)
    id_eitaa = models.CharField(max_length=50, verbose_name='آیدی ایتا شرکت', null=True, blank=True)

    twitter = models.URLField(verbose_name='آدرس توییتر شرکت', null=True, blank=True)
    id_twitter = models.CharField(max_length=50, verbose_name='آیدی توییتر شرکت', null=True, blank=True)



    def __str__(self):
        return self.email
