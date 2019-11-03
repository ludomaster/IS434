import numpy as np
import pandas as pd
import matplotlib as plt
from pandas import DataFrame

dataset = pd.read_csv("reditt-ML.csv")
df = pd.DataFrame(dataset)

r = (df.loc[df["risk"] == -1])
g = (df.loc[df["risk"] == 0])

df2 = [r, g]
result = pd.concat(df2)

x1 = result.iloc[:, :-1].values
y1 = result.iloc[:, -1].values

#c = pd.DataFrame(a)

from sklearn.preprocessing import LabelEncoder, OneHotEncoder
labelencoder_x1 = LabelEncoder()
x1[:,0] = labelencoder_x1.fit_transform(x1[:,0])
c = pd.DataFrame(x1)

onehotencoder = OneHotEncoder(categorical_features=[0])
x1 = onehotencoder.fit_transform(x1).toarray()
#d = pd.DataFrame(a)

labelencoder_y1 = LabelEncoder()
y1 = labelencoder_y1.fit_transform(y1)

#onehotencoder_y = OneHotEncoder(categorical_features=[0])
#y = onehotencoder_y.fit_transform(y).toarray()
#z = pd.DataFrame(y)

#e = d.iloc[:, :-1].values
#f = d.iloc[:, -1].values

x = pd.DataFrame(x1)
y = pd.DataFrame(y1)

np.random.seed(0)
from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size = 0.25, random_state = 0)

from sklearn.preprocessing import StandardScaler 
sc = StandardScaler()
x_train = sc.fit_transform(x_train)
x_test = sc.fit_transform(x_test)

#f = pd.DataFrame(y_pred)

#from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
#from sklearn.ensemble import RandomForestClassifier
#classifier = RandomForestClassifier(n_estimators = 20, criterion = 'entropy', random_state = 0)
#classifier = SVC(kernel = "linear", random_state = 0)
classifier = DecisionTreeClassifier(criterion = 'entropy', random_state=0)
#classifier.fit(x_train, y_train)
#classifier.fit(x_train, y_train[1])
classifier.fit(x_train, y_train)

## Prediting the classifier
y_pred = classifier.predict(x_test)

## Confusion_Matrix
from sklearn.metrics import confusion_matrix
cm = confusion_matrix(y_test, y_pred)

from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report

print(accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))







