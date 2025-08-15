text = ["esto"]

def translate(text):
    if not isinstance(text, str):                           
        if text is None:                                    
            return ""                                       
        text = str(text)  
        print(text)