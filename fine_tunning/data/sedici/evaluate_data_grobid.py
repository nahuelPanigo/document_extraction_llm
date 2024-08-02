from bs4 import BeautifulSoup
import re

class File:

    xml=None
    id = None
    soup = None
    sedici_type=None 

    def __init__(self,axml,aid,type):
        self.xml =axml
        self.id= aid
        self.soup = BeautifulSoup(self.xml, "lxml")
        self.sedici_type = type

    def get_soup(self):
        return self.soup()
    
    def get_abstract(self):
        try:
            return self.soup.find_all("abstract")[0].text
        except:
            None

    def get_title(self):
        try:
            return self.soup.find_all("teiHeader").find_all("title")[0].text
        except:
            None

    #def get_subtitle(self):
        
    def get_languaje(self):
        try:
            return self.soup.find("teiHeader").get('xml:lang')
        except:
            return None

    def get_type(self):
        return self.sedici_type
    
    def get_subtype(self):
        subtypes={
        "Tesis" : ['Tesis de grado','Tesis de doctorado','Tesis de maestria'],
        "Reporte": ['Reporte tecnico'],
        "Articulo": ['Articulo','Preprint','Documento de trabajo'],
        "Objeto de conferencia" : ['Objeto de conferencia','Articulo','Comunicacion']}
        possible_subtypes = subtypes.get(self.sedici_type, [])
        for subtype in  possible_subtypes:
            pattern = re.compile(re.escape(subtype), re.IGNORECASE)
            if pattern.search(str(self.soup)):
                return subtype
        return possible_subtypes[0]

    #def get_note(self):
    
    def get_date(self):
        try:
            return self.soup.find("publicationStmt").find("date").text
        except:
            return None

    def get_subjects(self):
        try:
            return [child.text for child in self.soup.find("keywords").find_all(recursive=False)]
        except:
            return None


    def get_author(self):
        author_tags = self.soup.find("biblstruct").find_all("author")
        authors = []
        for author_tag in author_tags:
            try:
                pers_name_tag = author_tag.find("persname")
                # Inicializar cadenas para nombres y apellidos
                surname_text = ""
                forename_text = ""
                
                # Obtener y concatenar todos los apellidos
                surnames = pers_name_tag.find_all("surname")
                for surname in surnames:
                    surname_text += surname.text + " "
                
                # Obtener y concatenar todos los nombres
                forenames = pers_name_tag.find_all("forename")
                for forename in forenames:
                    forename_text += forename.text + " "
                
                # Eliminar el espacio final de los apellidos y nombres
                surname_text = surname_text.strip()
                forename_text = forename_text.strip()
                
                # Formatear el nombre completo como "Apellido, Nombre"
                if surname_text and forename_text:
                    final_name = f"{surname_text}, {forename_text}"
                    authors.append(final_name)
            except:
                print("error format author div")
            
        return authors


    def to_dict(self):
       return { 
            "dc.date.issued" : self.get_date(),
            "dc.description.abstract" : self.get_abstract(),
            "sedici.subtype" : self.get_subtype(),
            "dc.type" : self.get_type(),
            "dc.title" : self.get_title(),
            "dc.languaje" : self.get_languaje(),
            "sedici.creator.person" : self.get_author()
        }


# class Articles(File):

#     file= None

#     def __init__ (self, afile):
#         self.file=afile
    
#     def get_issn():
    
#     def get_journal_title():
    
#     def get_journal_volume_and_issue():
            
#             "sedici.description.peerReview",         #ver
#         "sedici.identifier.issn",                #ok  <body><note><p>   puede no estar
#         "sedici.relation.journalTitle",          #ok  ver no aparece en xml  puede no estar
#         "sedici.relation.journalVolumeAndIssue"  #ok  <body><note><p>  puede no estar

    
class Tesis(File):


    def __init__(self, axml, aid, type):
        super().__init__(axml, aid, type)


    def get_director():
    


        # "sedici.contributor.director",
        # "thesis.degree.name",
        # "thesis.degree.grantor",
        # "sedici.date.exposure",
        # "sedici.description.note"