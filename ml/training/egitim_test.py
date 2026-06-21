"""Geriye uyumlu eğitim komutu.

Yeni eğitim hattı ``train_models.py`` içindedir. Bu dosya eski komutu kullanan
kişiler için aynı işlemi başlatır.
"""

try:
    from training.train_models import main
except ModuleNotFoundError:  # ``python ml/training/egitim_test.py`` kullanımı
    from train_models import main


if __name__ == "__main__":
    main()
