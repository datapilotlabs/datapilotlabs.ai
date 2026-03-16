from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout,get_user_model
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
User = get_user_model()
#Home page
def home_view(request):
    clients = User.objects.count()
    return render(request, 'home.html',{'clients':clients})
    
# LOGIN VIEW
def login_view(request):
    if request.method == "POST":

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')

        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'login.html')
# SIGNUP VIEW
def signup_view(request):

    if request.method == "POST":

        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.save()

        messages.success(request, "Account created successfully")
        return redirect('login')

    return render(request, 'signup.html')


# DASHBOARD
@login_required
def dashboard(request):

    return render(request, 'dashboard.html', {'username': request.user.username})


# LOGOUT
def logout_view(request):

    logout(request)
    return redirect('login')

def about_view(request):
    return render(request, 'about.html')
def contact_view(request):
    return render(request,'contact.html' )
def port_view(request):
    return render(request, 'port.html')


#python backend logic for smartclean
import pandas as pd
import numpy as np
import os
import plotly.express as px

from django.shortcuts import render
from django.core.files.storage import FileSystemStorage


def smart_clean(request):

    context = {}

    if request.method == "POST" and request.FILES.get("dataset"):

        dataset = request.FILES["dataset"]

        fs = FileSystemStorage()
        filename = fs.save(dataset.name, dataset)
        file_path = fs.path(filename)

        # -----------------------------
        # Detect dataset format
        # -----------------------------
        if filename.endswith(".csv"):
            df = pd.read_csv(file_path)

        elif filename.endswith(".xlsx"):
            df = pd.read_excel(file_path)

        elif filename.endswith(".json"):
            df = pd.read_json(file_path)

        else:
            context["error"] = "Unsupported file format"
            return render(request, "smartclean.html", context)

        # -----------------------------
        # DATASET PREVIEW
        # -----------------------------
        context["preview"] = df.head(10).to_html(classes="table table-striped", index=False)

        # -----------------------------
        # COLUMN TYPE DETECTION
        # -----------------------------
        column_types = {}

        for col in df.columns:

            if pd.api.types.is_numeric_dtype(df[col]):

                if pd.api.types.is_integer_dtype(df[col]):
                    column_types[col] = "Integer"
                else:
                    column_types[col] = "Decimal"

            else:
                column_types[col] = "Text"

        context["column_types"] = column_types

        # -----------------------------
        # AUTO MISSING VALUE PREDICTION
        # -----------------------------
        for col in df.columns:

            # Numeric columns
            if pd.api.types.is_numeric_dtype(df[col]):

                df[col].fillna(df[col].median(), inplace=True)

            # Text columns
            else:

                if not df[col].mode().empty:
                    df[col].fillna(df[col].mode()[0], inplace=True)
                else:
                    df[col].fillna("Unknown", inplace=True)

        # -----------------------------
        # ORIGINAL ROW COUNT
        # -----------------------------
        original_rows = df.shape[0]

        # -----------------------------
        # REMOVE DUPLICATES
        # -----------------------------
        df = df.drop_duplicates()

        # -----------------------------
        # REMOVE OUTLIERS (IQR METHOD)
        # -----------------------------
        numeric_cols = df.select_dtypes(include=np.number).columns

        for col in numeric_cols:

            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)

            IQR = Q3 - Q1

            lower = Q1 - (1.5 * IQR)
            upper = Q3 + (1.5 * IQR)

            df = df[(df[col] >= lower) & (df[col] <= upper)]

        cleaned_rows = df.shape[0]

        removed_rows = original_rows - cleaned_rows

        improvement = (removed_rows / original_rows) * 100

        quality_score = 100 - improvement

        # -----------------------------
        # DATA PROFILING
        # -----------------------------
        context["summary"] = df.describe().to_html(classes="table", index=True)

        # -----------------------------
        # DATASET REPORT
        # -----------------------------
        report = {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "missing": df.isnull().sum().sum(),
            "duplicates": df.duplicated().sum()
        }

        context["report"] = report

        # -----------------------------
        # INTERACTIVE CHART
        # -----------------------------
        numeric_cols = df.select_dtypes(include=np.number).columns

        if len(numeric_cols) > 0:

            fig = px.histogram(df, x=numeric_cols[0])

            context["chart"] = fig.to_html()

        # -----------------------------
        # SAVE CLEANED DATASET
        # -----------------------------
        cleaned_filename = "cleaned_" + filename
        cleaned_path = os.path.join(fs.location, cleaned_filename)

        df.to_csv(cleaned_path, index=False)

        # -----------------------------
        # UPDATE CONTEXT
        # -----------------------------
        context.update({
            "original_rows": original_rows,
            "clean_rows": cleaned_rows,
            "rows_removed": removed_rows,
            "improvement": round(improvement, 2),
            "quality_score": round(quality_score, 2),
            "download_file": fs.url(cleaned_filename)
        })

    return render(request, "smartclean.html", context)

#visulization dashboard
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff

from django.shortcuts import render
from django.core.files.storage import FileSystemStorage


def data_dashboard(request):

    context = {}

    if request.method == "POST" and request.FILES.get("dataset"):

        dataset = request.FILES["dataset"]

        fs = FileSystemStorage()
        filename = fs.save(dataset.name, dataset)
        file_path = fs.path(filename)

        # -----------------------------
        # READ DATASET
        # -----------------------------
        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(file_path)

            elif filename.endswith(".xlsx"):
                df = pd.read_excel(file_path)

            else:
                context["error"] = "Unsupported file format"
                return render(request, "visual.html", context)

        except Exception as e:
            context["error"] = f"Error reading file: {str(e)}"
            return render(request, "visual.html", context)

        # -----------------------------
        # CHECK EMPTY DATASET
        # -----------------------------
        if df.empty:
            context["error"] = "Dataset is empty"
            return render(request, "visual.html", context)

        # -----------------------------
        # SORTING FILTER
        # -----------------------------
        sort_column = request.POST.get("column")

        if sort_column and sort_column in df.columns.tolist():
            df = df.sort_values(by=sort_column)

        # -----------------------------
        # DATASET PREVIEW
        # -----------------------------
        context["preview"] = df.head(10).to_html(
            classes="table table-striped", index=False
        )

        context["columns"] = df.columns.tolist()

        # -----------------------------
        # NUMERIC COLUMNS
        # -----------------------------
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

        # -----------------------------
        # HISTOGRAM
        # -----------------------------
        if len(numeric_cols) > 0:

            col = numeric_cols[0]

            fig1 = px.histogram(df, x=col, title="Histogram")
            context["histogram"] = fig1.to_html()

            # BAR CHART
            fig2 = px.bar(df.head(10), y=col, title="Bar Chart")
            context["bar_chart"] = fig2.to_html()

            # BOX PLOT
            fig3 = px.box(df, y=col, title="Box Plot")
            context["box_plot"] = fig3.to_html()

            # LINE CHART
            fig4 = px.line(df.head(50), y=col, title="Line Chart")
            context["line_chart"] = fig4.to_html()

        # -----------------------------
        # SCATTER PLOT
        # -----------------------------
        if len(numeric_cols) >= 2:

            fig5 = px.scatter(
                df,
                x=numeric_cols[0],
                y=numeric_cols[1],
                title="Scatter Plot"
            )

            context["scatter"] = fig5.to_html()

        # -----------------------------
        # CORRELATION HEATMAP
        # -----------------------------
        if len(numeric_cols) >= 2:

            corr = df[numeric_cols].corr()

            heatmap = ff.create_annotated_heatmap(
                z=corr.values,
                x=list(corr.columns),
                y=list(corr.index),
                annotation_text=np.round(corr.values, 2),
                showscale=True
            )

            context["heatmap"] = heatmap.to_html()

    return render(request, "visual.html", context)