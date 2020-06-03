# Candidacy Exercise 

In this repository you can find the tool I have writen. 
The repository includes the following folder:
An objects folder which contains the objects Iv'e writen: Firmware_File, Model, Brand.
An Exceptions folder which contains two custom Exceptions Iv'e created: ParsingError and DBConnectionError.
The other files are the main, web_crawler, page_parser and mongo_wrapper.
Each time the code runs there is a .log file created with the name: 'web_crawler_(current time).log'

## Prerequisites

Make sure MongoDB is currently running on your machine with default properties (localhost:27017) before running the code.
Invoke the tool by running the following line:

```
python3 main.py "https://www.rockchipfirmware.com/"
```

## Overview Of the files

### Firmware_File

This object contains a dictionary which holds the metadata of the file.

Note: On my machine it was not possible to download over 250 zip files (each +200MB) so my code currently does not download 
      the zip files but instead saves their URL to use them in the future. With that being said, my code *does* have the 
      relevant functionality to upload, download and delete the zip files if necessary.

### Model

This objects holds a name of a model as well as all its available firmware files on the website, so If necessary we can question the database and get information concerning this model.

### Brand

This objects holds a name of a brand as well as all its available models on the website, so If necessary we can question the database and get information concerning this brand.

### ParsingError

The error indicates something went wrong while parsing the page with a proper message to the .log file.

### DBConnectionError

The error indicates something went wrong while connecting to the database with a proper message to the .log file.

### WebCrawler

The web crawler is the main part of my solution, It iterates every URL from the given website and parses the information.
If needed, the scrawler updated relevant data in the database.

### MongoWrapper

The mongo wrapper contains all the functionality of Create, Reade, Update and Delete that is needed for the crawler to manage the firmware files metadata.

### PageParser

The page parser contains five functions (four are in use at the moment, the fifth is "download_file" which is not currently used, see Firmware_File Note). 
The website my tool is crawling has a main tag called "article" which contains all of the file's metadata.
The structure of the article is as follows:
```
<article class="art-post art-article">
  <div class="group-header">
  <div class="group-left">
  <div class="group-right">
  <div class="group-footer">
</article>
 ```
That is why the parser has four main functions: parser_header, parse_footer, parse_sides(gets which side to parse as an argument).

Parse Header Explanation:
First the function retrieves the div which is the header part of the page.
After checking the page and It's structure Iv'e come to the conclusion that 
the best way to retrieve the file's metadata in the most generic way is by 
a class name each of them is given.
There are only two possible name formats: 1. field-name-(name of field)
                                          2. field-name-field-(name of field)
so the parse_header function iterates every div that has a class with the first 
format and then It checks whether the class name matches the first format or 
second and that way It extracts the Key of the metadata.
key extraction: field['class'] contains all of the classes of the current div
for example: ['field', 'field-name-title', 'field-type-ds', 'field-label-hidden']
the one we want to parse is in the second cell of the list therefore it searches
for the pattern in field['class'][1] (=field-name-title), then the key itself is the
first value in the returned value from search function (name_of_field_option2.search(field['class'][1])->[1]<-)
The value is held inside a div with a class named "field-item even" so it extracts
it from there, then the key and value are added to the firmware_file object metadata.

The other parsers are writen in a similar manner.
