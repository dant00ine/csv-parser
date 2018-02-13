
var isAdvancedUpload = function() {
    var div = document.createElement('div');
    return ('draggable' in div) || ('ondragstart' in div && 'ondrop' in div) && 'FormData' in window && 'FileReader' in window;
}()

var $file_area = $('.file__area');
var $form = $('form')

if (isAdvancedUpload) {
    $file_area.addClass('has-advanced-upload');

    var droppedFiles = {};

    $file_area.on('drag dragstart dragend dragover dragenter dragleave drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
      })
      .on('dragover dragenter', function() {
        $(this).addClass('is-dragover');
      })
      .on('dragleave dragend drop', function() {
        $(this).removeClass('is-dragover');
      })
      .on('drop', function(e) {
        e.stopPropagation();
        e.preventDefault();
        var files = e.originalEvent.dataTransfer.files; 
        updateFilePreview(files[0].name, $(this).attr('id'));
        droppedFiles[$(this).attr('id') + '-csv'] = files[0];
      });   
}

function updateFilePreview(newFileName, divID) {
    $(`#${divID} .file__graphic`).html(`<p> ${newFileName} </p>`);
}

$(function(){
    $('input:file').change(function(){
        var fileName = $(this).val();
        fileName = fileName.replace('C:\\fakepath\\', '');
        divID = $(this).attr('id').replace('-csv', '');
        // delete droppedFiles[fileName]; // have to prevent duplicate uploads
        updateFilePreview(fileName, divID);
    })
})

$form.on('submit', function(e){
    if($form.hasClass('is-uploading')) return false;
    $form.addClass('is-uploading').removeClass('is-error');

    if (isAdvancedUpload) {
        // ajax for modern browsers
        e.preventDefault();

        var ajaxData = new FormData($form.get(0));

        if (droppedFiles) {
            $.each( droppedFiles, function(i, file) {
                ajaxData.append(i, file);
            });
        }

        $.ajax({
            url: $form.attr('action'),
            type: $form.attr('method'),
            data: ajaxData,
            cache: false,
            contentType: false,
            processData: false,
            complete: function() {
                $form.removeClass('is-uploading');
            },
            success: function(response, textStatus, jqXHR) {
                $form.addClass( textStatus == 'success' ? 'is-success' : 'is-error' );
                saveData(response, jqXHR.getResponseHeader('Filename'))
                getSMS(jqXHR.getResponseHeader('SMS-Filepath'))
            },
            error: function(response, textStatus, jqXHR) {
                $form.removeClass('is-uploading').addClass('is-error');
                if(response.responseJSON && response.responseJSON.message)
                    errorHTML(response.responseJSON.message)
            }
        });
    } else {
        console.log("legacy browser detected")
        // ajax for legacy browsers
    }
});

function getSMS(fileUrl){
    $.get("/get_sms?filepath="+ encodeURIComponent(fileUrl), function(res, status, XHR){
        saveData(res, XHR.getResponseHeader('Filename'))
    })
    .fail(function(response, textStatus, jqXHR){
        $form.removeClass('is-uploading').addClass('is-error');
        if(response.resopnseJSON && response.responseJSON.message)
            errorHTML(response.responseJSON.message)
    })
}

function errorHTML(msg){
    $('.error_message').html(`
        <h5> ERROR </h5>
        <p>${msg}</p>
    `)
    .css('background-color', '#F0D9D9')
    .css('border', '1px solid #cc0000')
}


const saveData = (function () {
    const a = document.createElement("a");
    document.body.appendChild(a);
    a.style="display: none;";
    return function (data, fileName) {
        const blob = new Blob([data], {type: "application/zip"});
        url = window.URL.createObjectURL(blob);
        a.href = url;
        a.download = fileName;
        a.click();
        window.URL.revokeObjectURL(url);
    };
}());