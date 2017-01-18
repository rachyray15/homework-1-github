def handleButton():
    print('Button Clicked')
b = qt.QPushButton('Push Me')
b.connect('clicked()', handleButton)
b.show()
