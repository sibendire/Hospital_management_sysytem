from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import LabTest, LabRequest, LabResult

from .forms import (
    LabTestForm,
    LabRequestForm,
    LabResultForm,
)



def laboratory_dashboard(request):


    context={

        "tests":LabTest.objects.count(),

        "requests":LabRequest.objects.count(),

        "pending":
        LabRequest.objects.filter(
            status="Pending"
        ).count(),

        "completed":
        LabRequest.objects.filter(
            status="Completed"
        ).count(),

    }


    return render(
        request,
        "laboratory/dashboard.html",
        context
    )







def test_list(request):

    tests=LabTest.objects.all()


    return render(
        request,
        "laboratory/test_list.html",
        {
            "tests":tests
        }
    )







def add_test(request):


    if request.method=="POST":

        form=LabTestForm(request.POST)


        if form.is_valid():

            form.save()

            return redirect("test_list")


    else:

        form=LabTestForm()



    return render(

        request,

        "laboratory/test_form.html",

        {
            "form":form
        }

    )








def create_lab_request(request):


    if request.method=="POST":

        form=LabRequestForm(request.POST)


        if form.is_valid():

            form.save()

            return redirect(
                "lab_requests"
            )


    else:

        form=LabRequestForm()



    return render(

        request,

        "laboratory/lab_request_form.html",

        {
            "form":form
        }

    )







def lab_requests(request):


    requests=LabRequest.objects.all()


    return render(

        request,

        "laboratory/lab_request_list.html",

        {
            "requests":requests
        }

    )









def enter_result(request,id):


    lab_request=get_object_or_404(

        LabRequest,

        id=id

    )


    if request.method=="POST":


        form=LabResultForm(request.POST)


        if form.is_valid():


            result=form.save(commit=False)


            result.lab_request=lab_request


            result.save()



            lab_request.status="Completed"

            lab_request.save()



            return redirect(
                "lab_requests"
            )


    else:

        form=LabResultForm()



    return render(

        request,

        "laboratory/result_form.html",

        {
            "form":form,
            "request":lab_request
        }

    )
@login_required
def patient_lab_results(request, patient_id):

    results = (
        LabResult.objects
        .select_related(
            "lab_request",
            "lab_request__test",
            "lab_request__patient",
        )
        .filter(
            lab_request__patient_id=patient_id,
            lab_request__status="Completed"
        )
        .order_by("-result_date")
    )

    data = []

    for result in results:

        data.append({
            "test": result.lab_request.test.name,

            "category": result.lab_request.test.category,

            "result": result.result,

            "interpretation": (
                result.interpretation
                or "No interpretation provided"
            ),

            "technician": result.technician,

            "sample_number": (
                result.lab_request.sample_number
            ),

            "date": result.result_date.strftime(
                "%d %b %Y %H:%M"
            ),
        })

    return JsonResponse(data, safe=False)