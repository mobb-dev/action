package com.securitywhitepapers.xxe;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;
import org.xml.sax.XMLReader;
import org.xml.sax.helpers.XMLReaderFactory;

public class XmlReader {

    public static void main(String[] args) throws SAXException, IOException {
        //VULNERABLE
        XMLReader reader = XMLReaderFactory.createXMLReader();  
//        HOW TO MAKE IT SAFE
//        reader.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
//        reader.setFeature("http://xml.org/sax/features/external-general-entities", false);
//        reader.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
//        reader.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
            
        reader.parse(new InputSource(new FileInputStream(new File("payload.xml"))));
    }
    
}
