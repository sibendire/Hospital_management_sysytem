from django import forms

from .models import (
    LabTest,
    LabRequest,
    LabResult
)



class LabTestForm(forms.ModelForm):

    class Meta:

        model = LabTest

        fields = [
            'name',
            'category',
            'price',
            'description'
        ]

        widgets = {

            'name': forms.TextInput(
                attrs={
                    'class':'form-control',
                    'placeholder':'Enter test name'
                }
            ),


            'category': forms.Select(
                attrs={
                    'class':'form-select'
                }
            ),


            'price': forms.NumberInput(
                attrs={
                    'class':'form-control',
                    'placeholder':'Enter price'
                }
            ),


            'description': forms.Textarea(
                attrs={
                    'class':'form-control',
                    'rows':3
                }
            ),

        }







class LabRequestForm(forms.ModelForm):


    class Meta:


        model = LabRequest


        fields = [

            'patient',
            'test',
            'sample_number',
            'requested_by'

        ]


        widgets = {


            'patient':forms.Select(

                attrs={
                    'class':'form-select'
                }

            ),



            'test':forms.Select(

                attrs={
                    'class':'form-select'
                }

            ),



            'sample_number':forms.TextInput(

                attrs={

                    'class':'form-control',

                    'placeholder':
                    'LAB-0001'

                }

            ),



            'requested_by':forms.TextInput(

                attrs={

                    'class':'form-control',

                    'placeholder':
                    'Doctor/Nurse name'

                }

            )


        }








class LabResultForm(forms.ModelForm):


    class Meta:


        model = LabResult


        fields = [

            'result',

            'interpretation',

            'technician'

        ]



        widgets = {


            'result':forms.Textarea(

                attrs={

                    'class':'form-control',

                    'rows':5,

                    'placeholder':
                    'Enter laboratory findings'

                }

            ),




            'interpretation':forms.Textarea(

                attrs={

                    'class':'form-control',

                    'rows':3,

                    'placeholder':
                    'Medical interpretation'

                }

            ),




            'technician':forms.TextInput(

                attrs={

                    'class':'form-control',

                    'placeholder':
                    'Laboratory technician'

                }

            )


        }