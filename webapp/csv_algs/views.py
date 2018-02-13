# standard libraries
import os
import io
import datetime
import logging

logger = logging.getLogger('django')

# Django libraries
from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.core import serializers

# file libraries
from django.core.files.storage import FileSystemStorage

# local libraries
from .csv_algorithms import CSVAlgs
from .models import Batch, File

# profiling
# from silk.profiling.profiler import silk_profile

def index(request):
    # fetch a list of the groups
    # batches = get_list_or_404(Batch)
    # batches = Batch.objects.order_by('-created_date')[:5]
    context = {
        # 'batches_list': batches
    }
    return render(request, 'csv_algs/index.html', context)

# TODO Potential feature: Archives
# manage past uploads at a glance!

# def index_batch(request):
#     batches = get_list_or_404(Batch)
#     data = serializers.serialize('json', batches)
#     return HttpResponse(data, content_type='application/json')

# def show_batch(request, batch_id):
#     # grab data for a specific batch and return JSON
#     try:
#         batch = Batch.objects.get(pk=batch_id)
#         data = serializers.serialize('json', batch)
#     except Batch.DoesNotExist:
#         raise Http404("Batch does not exist")
#     return HttpResponse(data, content_type='application/json')

def create(request):
    fileUrls = {}
    fs = FileSystemStorage()

    if 'mail-maga-csv' not in request.FILES or 'no-mail-csv' not in request.FILES:
        errorMessage = '2 files needed: 2 files needed: <strong> no-mail list </strong> and <strong> mail maga list</strong>'
        logger.exception(errorMessage)
        return JsonResponse({
            'message': errorMessage
        }, status=400)

    for name, file_data in request.FILES.items():
        try:
            uploaded_file_url = _saveFile(name, file_data, fs)
            fileUrls[name] = settings.MEDIA_ROOT + uploaded_file_url
        except:
            logger.exception('''Error code 500, file could not be written,
             this is most likely a server file permissions error.''')
            return JsonResponse({
            'message': '''Error code 500, file could not be written,
             this is most likely a server file permissions error.'''
        }, status=500)

    if 'eccube-csv' not in fileUrls: #ECCube なしでもOK!
        fileUrls['eccube-csv'] = None

    #instantiate CSVAlgs class to use for data processing
    csvHelper = CSVAlgs(fileUrls['mail-maga-csv'],
                    fileUrls['no-mail-csv'],
                    fileUrls['eccube-csv'])

    try: #calling processes that will generate output files
        csvFilePath = csvHelper.retrieveSMSOutput() or 'false'
        mailMagaFile = open(csvHelper.retrieveMailMagaOutput())
    except Exception as exc: #possible errors defined in csv_exceptions.py
        logger.exception(exc.message)
        return JsonResponse({
            'message': exc.message
        }, status=400)

    response = HttpResponse(mailMagaFile, content_type="text/csv")
    response['Content-Disposition'] = 'attachment'
    response['Filename'] = os.path.basename(mailMagaFile.name)
    response['SMS-Filepath'] = csvFilePath
    logger.info(f"succesfully output file {os.path.basename(mailMagaFile.name)}")
    return response

# --> File URL (throws)
def _saveFile(name, file_data, fs):
    fs.delete(settings.MEDIA_ROOT + name) # delete prior failed uploads
    filename = fs.save(name, file_data)
    return fs.url(filename)

# --> follow up URL for second file download 
# (file has already been generated)
def get_sms(request):
    sms_file_path = request.GET.get('filepath', None)
    print(sms_file_path)
    try:
        sms_file = open(sms_file_path)
    except:
        return JsonResponse({
        'message': '''Please contact your system administrator.
         The SMS output file was not able to be read by the system.
          This could be a file permissions error'''
    }, status=500)
    response = HttpResponse(sms_file, content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename=smsOutput.csv"'
    response['Filename'] = os.path.basename(sms_file.name)
    logger.info(f"successfully output file {os.path.basename(sms_file.name)}")
    return response
    raise Http404