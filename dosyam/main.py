import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, matthews_corrcoef, cohen_kappa_score, confusion_matrix, ConfusionMatrixDisplay

def generate_data():
    # 1 ile 1000 arasında sayılar üret
    X = np.arange(1, 1001).reshape(-1, 1)
    y = np.array([1 if x % 2 == 0 else 0 for x in X.flatten()])  # 1: çift, 0: tek
    return X, y

def generate_test_data():
    # 800 ile 1300 arasında sayılar üret
    test_X = np.arange(800, 1301).reshape(-1, 1)
    return test_X

def train_model(X, y):
    # Modeli eğit
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)
    return model

def evaluate_model(model, test_X):
    # Tahmin yap
    predictions = model.predict(test_X)
    return predictions

def main():
    # Model eğitimi
    X, y = generate_data()
    model = train_model(X, y)

    # Test verisi
    test_X = generate_test_data()
    predictions = evaluate_model(model, test_X)

    # Performans değerlendirmesi
    test_y = np.array([1 if x % 2 == 0 else 0 for x in test_X.flatten()])  # Gerçek değerler
    f1 = f1_score(test_y, predictions)
    mcc = matthews_corrcoef(test_y, predictions)
    kappa = cohen_kappa_score(test_y, predictions)

    print(f"F1 Skoru: {f1:.2f}")
    print(f"MCC: {mcc:.2f}")
    print(f"Kappa: {kappa:.2f}")

    # Konfizyon matrisini hesapla
    cm = confusion_matrix(test_y, predictions)
    print("Konfizyon Matrisi:")
    print(cm)

    # Konfizyon matrisini görselleştir
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Tek', 'Çift'])
    disp.plot(cmap=plt.cm.Blues)
    plt.title('Konfizyon Matrisi')
    plt.show()

if __name__ == "__main__":
    main()