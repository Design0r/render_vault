sidebar_style = """
QWidget{
    background-color: rgb(38,38,38);
    color: rgb(255,255,255);
}

QPushButton{
    background-color: none;
    border-radius: 5px;
}

QPushButton::hover{
    background-color: rgb(235, 177, 52);
}

QPushButton::checked{
    background-color: rgb(235, 177, 52);
}
"""

toolbar_style = """
QWidget{
    background-color: rgb(50,50,50);
}

QPushButton{
    background-color: none;
    border-radius: 5px;
}

QPushButton::hover{
    background-color: rgb(235, 177, 52);
}

QComboBox, QAbstractItemView{
    background-color: rgb(38,38,38);
    font-size: 10pt;
    border-radius: 5px;
    border: 1px solid black;
    color: white;
}

QLineEdit{
    background-color: rgb(38,38,38);
    font-size: 10pt;
    border-radius: 5px;
    border: 1px solid black;
    margin-right: 10px;

}



QLabel{
    font-size: 16pt;
    color: white;
}
"""
