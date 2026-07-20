'use strict'
/**
 * @fileoverview business/view_components/file_upload_view.js
 * FileUpload view component class.
 * 
 * usage:
 * <code>
 * </code>
 * 
 * @author huma@thinkxinc.com (Huma Farheen)
 */


/**
 * FileUploadView Showing State Enum.
 */
const FileUploadViewShowingState = Object.freeze({
    onhide: 0,
    onshow: 1,
});


/**
 * FileUploadView Upload State Enum.
 */
const FileUploadViewUploadState = Object.freeze({
    onready: 0,
    onuploading: 1,
    onuploadcompleted: 2,
    onuploadfailed: 2,
});

const FileType = Object.freeze({
    pdf: '/img/icons/file_types/pdf_file.png',
    jpg: '/img/icons/file_types/jpg_file.png',
    png: '/img/icons/file_types/png_file.png',
    txt: '/img/icons/file_types/txt_file.png',
    aiff: '/img/icons/file_types/aiff_file.png',
    wav: '/img/icons/file_types/wav_file.png'
});

/**
 * FileUploadTableViewCell component class.
 * @constructor
 * @classdesc `<ul class=fileUploadTableViewCell id={id}></ul>` is necessary in HTML.
 * usage:
 * `<code>`
 *  var cell = new FileUploadTableViewCell(table_view_id, index_of_cell);  // insert to table automatically
 *  cell.content = content; // update html automatically
 * `</code>`
 * @param {string} id - The DOM id where this view is inserted.
 */
class FileUploadTableViewCell {
    __template__ = `\
    <div id=$id class=uploadFileTableViewCell>
        <img src=$uploadedFileTypeIcon/> 
        <div class = uploadProgressDetails style= "border:2px;">
            <div class = fileNameAndPercentage style= "border:2px;">
                <div style = "text-overflow: ellipsis; padding-right:20px">$uploadedFileName</div>
                <div class = "uploadStatusIndicator">$uploadStatusIndicator</div>
        </div>
            <div id="uploadIndicatorContainer">
                    <div id="uploadIndicator" class = "uploadIndicator">
                    </div>
            </div>            
        </div>
        <div id= "uploadCancelButton" class="close-icon">
        </div>
    </div>
    `;

    // settings
    __id__ = null;
    __table_view_id__ = null;
    __index__ = null;
    __uploadedFileName__ = null;
    __uploadedFileTypeIcon__ = null;

    // values
    _content = {};
    index = null;

    //constructor(table_view_id, index, content) {
    constructor(table_view_id, index) {
        // set veiw id
        this.__table_view_id__ = table_view_id;
        this.__index__ = index;
        this.__id__ = `${table_view_id}_${index}`

        // set elements
        this._setElements();
    }

    /**
     * content setter.
     */
    set content(uploadedFileName) {
       this.__uploadedFileName__ = uploadedFileName;
       this.__uploadedFileTypeIcon__ = '/img/icons/file_types/pdf_file.png';
       this._resetCell();
       this._setElements();
    }
    
    set state(state) {

        // set state of upload indicator
        this.$uploadIndicator.style.width = state
        this.$uploadStatusIndicator.innerHTML = state
           
    }

    /**
     * DOM nodes as variables.
     */
    _setElements() {
        this.$tableView = document.getElementById(this.__table_view_id__);
        if (this.$tableView == null) {
            console.warn(`<ul id=${this.__table_view_id__}></ul> not found.`);
        }
        console.log(this.$tableView)
        
        
    }

    /**
     * Initialize the layout for display.
     */
    _initLayout() {
    }
    /* private functions */

    /**
     * Reset cell content.
     */
    _resetCell() {
        // set texts by this._content
        this.__template__ = this.__template__.replace('$id', this.__id__);
        this.__template__ = this.__template__.replace('$uploadedFileTypeIcon', this.__uploadedFileTypeIcon__);
        this.__template__ = this.__template__.replace('$uploadedFileName', this.__uploadedFileName__);  
        this.$tableView.innerHTML += this.__template__;
        this.$cellView = document.getElementById(this.__id__);
        if (this.$cellView == null) {
            console.warn(`<li id=${this.__id__} class=fileUploadTableViewCell></li> not found.`);
        }
        this.$uploadStatusIndicator = this.$cellView.querySelector('.uploadStatusIndicator');
        this.$uploadIndicator = this.$cellView.querySelector('.uploadIndicator');
        this.$uploadCancelButton = this.$cellView.querySelector('.close-icon');
    }

    /* public functions */
    hide() {
        console.log(`hide function called in ${this.__id__}`);
        document.getElementById(this.__id__).classList.add('fadeOutToLeft');
    }
}

/**
 * FileUploadView component class.
 * @constructor
 * @classdesc `<div id={id} class=fileUploadView>` is necessary in HTML.
 * usage:
 * `<code>`
 *     documentUploadView = new FileUploadView(
 *         'documentUploadView',
 *         [FileExtension.png, FileExtension.jpg]
 *         )
 * `</code>`
 * @param {string} id - The DOM id where this view is set.
 * @param {list of FileExtension} acceptable_file_extensions - eg. [FileExtension.jpg, FileExtension.png]
 * @param {string} title - title text
 * @param {string} subtitle - subtitle text
 * @param {string} dropTitle - drag & drop area title text
 * @param {string} or - drag & drop area OR text
 * @param {string} browseButtonTitle - browse file button text
 * @param {string} uploadedFilesTableTitle - uploadFilesTable title
 */
class FileUploadView {
    __inner_template__ = `
        <div class=fileUploadView>
            <h3 class=title style="text-align: center;">$title</h3>
            <p class=subtitle style="text-align: center;">$subtitle</p>
            <div class=dropArea>
                <img class=dropImage/>
                <h5 class=dropTitle>$dropTitle</h5>
                <p class=or>$or</p>
                <label style="padding:20px;">
                <input type="file" id ="upload" class="browseButton" style="display: none;" />
                <span class=browseButton>$browseButton</span>
                </label>
            </div>
            <div id =uploadedFilesTable><div>
        </div>
    `
   
    __upload_file_table_title__ = `<h3 class=uploadedFilesTableTitle>$uploadedFilesTableTitle</h3>` 
    __acceptable_file_extensions__ = ['jpg', 'png', 'pdf', 'wav', 'aiff', 'mp3']

    __id__ = null;
    __requested_file_extensions__ = null;

    __title__ = null;
    __subtitle__ = null;
    __dropTitle__ = null ;
    __browseButtonTitle__ = null;
    __or__ = null;
    __uploadedFilesTableTitle__ = null;
    _cells__ = [];
    __cell_index__ = 0;
    __uploadedFilesTableId__ = 'uploadedFilesTable'; 

    // states
    _showingstate = null;
    _uploadstate = null;

    // data
    _file = null;

    constructor(
        id, requested_file_extensions,
        title, subtitle, or, browseButtonTitle, dropTitle ,
        uploadedFilesTableTitle
        ) {
        // set 
        this.__id__ = id;
        this.__title__ =  title;
        this.__subtitle__ = subtitle;
        this.__requested_file_extensions__ = requested_file_extensions;
        this.__dropTitle__ = dropTitle ;
        this.__browseButtonTitle__ = browseButtonTitle;
        this.__or__ = or;
        this.__uploadedFilesTableTitle__ = uploadedFilesTableTitle

        // validate acceptable file extensions format
        if (this.__requested_file_extensions__)
        if (!Array.isArray(this.__requested_file_extensions__)) {
            console.error(`
                __acceptable_file_extensions__ must be type of array,
                but ${typeof this.__requested_file_extensions__}`);
        } else if (this.__requested_file_extensions__.length == 0) {
            console.error(`__acceptable_file_extensions__ must not be empty`);
        }
     
        // validate acceptable file extensions 
        this.__requested_file_extensions__.forEach((elem) => {
            if (this.__acceptable_file_extensions__.indexOf(elem) === -1) {
                console.error('unacceptable file');
            }
        });

        // TODO: other validations

        // set html elements
        document.getElementById(id).innerHTML = this.__inner_template__
            .replace('$title', title)
            .replace('$subtitle', subtitle)
            .replace('$or', or)
            .replace('$dropTitle', dropTitle)
            .replace('$browseButton', browseButtonTitle)
            ;

        // initialize view elements
        this._setElements();
        // set eventhandlers
        this._setEventHandlers();
    }

    /**
     * showing state setter.
     */
    set showingstate(showingstate) {
        this._showingstate = showingstate;
        switch (state) {
            case FileUploadViewShowingState.onhide:
                console.log(`FileUploadView ${this.__id__} showing state changed -> onhide`);
                break
            case FileUploadViewShowingState.onshow:
                console.log(`FileUploadView ${this.__id__} showing state changed -> onshow`);
                break
        }
    }

    /**
     * showing state getter.
     */
    get showingstate() {return this._showingstate}

    /**
     * upload state setter.
     */
    set uploadstate(uploadstate) {
        this._uploadstate = uploadstate;
        switch (state) {
            case FileUploadViewUploadState.onready:
                break
        }
    }

    /**
     * upload state getter.
     */
    get uploadstate() {return this._uploadstate}

    /**
     * DOM nodes as variables.
     */
    _setElements() {
        // fileUploadView
        this.$fileUploadView = document.getElementById(this.__id__);
        if (this.$fileUploadView == null) {
            console.warn(
                `<section id=${this.__id__} class=fileUploadView></section> is necessary in HTML.`);
        }
        // title
        this.$title = this.$fileUploadView.querySelector('.title');
        if (this.$title == null) {
            console.warn(
                `<h6 class=title> is necessary in HTML.`);
        }
        this.$dropArea = this.$fileUploadView.querySelector('.dropArea');
        if (this.$dropArea == null) {
            console.warn(
                `<div class=dropArea>is necessary in HTML.`);
        }
        this.$browseButton = document.getElementById('upload');
        if (this.$browseButton == null) {
            console.warn(
                `<div class=dropArea>is necessary in HTML.`);
        }
      
        // TODO: other validations
    }

    /**
     * Initialize the layout for display.
     */
    _initLayout() {
    }

    /**
     * Set event handlers.
     */
    _setEventHandlers() {
        const _this = this;
   
        // dragover event handler
        this.$dropArea.addEventListener('dragover', (e) => {
            console.log(`a file is dropped down on the droparea.`); 
   
            e.preventDefault();
        });
        
        // drop event handler
        this.$dropArea.addEventListener('drop', (e) => {
            console.log(`a file is dropped down on the droparea.`);  

            const files = e.dataTransfer.files;

            // Get a reference to the file
            var file = files[0];

            // Get a reference to the filename
            var filename = file.name;

            //Add file cell to table
            this._addFileUploadCell(file, filename)

            e.preventDefault(); 
        });  

        // browse button handler
        this.$browseButton.onchange = () => {
            const file = this.$browseButton.files[0];
            var data = new FormData();

            // Create a XMLHTTPRequest instance
            var request = new XMLHttpRequest();

            request.responseType = "json";

            // Get a reference to the filename
            var filename = file['name'];
            this._addFileUploadCell(file, filename);
        }

        //TODO : function to get file icon by type 
        function getFileTypeEnumKeys(fileType) {
            return Object.keys(FileType);
          }

    }

    _addFileUploadCell(file, fileName){

        // fetch file extension
        const ext = getFileExtension(fileName);

        // add file upload cell to table
        var cell = new FileUploadTableViewCell(this.__uploadedFilesTableId__, this.__cell_index__);
        cell.content = fileName;
        this._setFileUploadCellEventHandler(cell)
        this._cells__.push(cell)
        this.__cell_index__ +=1;

        // used for the purpose of upload indicator demo
        var width = 1;
        var identity = setInterval(scene, 50);
        function scene() {
          if (width >= 100) {
            clearInterval(identity);
          } else {
            width++; 
            cell.state = width + '%'; 
          }
        }

        // function to get file extension
        function getFileExtension(fileName){ 
            const lastDot = fileName.lastIndexOf('.');

            const ext = fileName.substring(lastDot + 1);
            return ext;
        }

        // function to upload to s3
        function getSignedRequest(file){
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/v1/organizations/documents/upload?file_name="+file.name+"&file_type="+file.type);

            // TODO: connect upload file to aws
            xhr.onreadystatechange = function(){
              if(xhr.readyState === 4){
                  console.log(xhr.status);
                if(xhr.status === 200){
                  var response = JSON.parse(xhr.responseText);
                  //TODO: progress bar state update
                }
                else{
                  alert("Could not get signed URL.");
                }
              }
            };
             xhr.send();
          }      
    }

    _setFileUploadCellEventHandler(cell){
        console.log(document.getElementById(cell.__id__));

    console.log(`set event for ${cell.__id__}`);
            currentCell = document.getElementById(cell.__id__);
            currentCell.querySelector('.close-icon').addEventListener('click', e => {
                console.log(`cell ${cell.__id__} clicked`);
                currentCell.remove()
                
            });
    }
    /* private functions */
}
