from flask import Flask, render_template, request, send_file
import os
import tempfile
import fitz  # PyMuPDF
import json

app = Flask(__name__)
TEMPLATE_PATH = os.path.join(os.getcwd(), 'pdf_templates', 'certificate_template_with_fields.pdf')

def get_pdf_fields(pdf_path):
    """Extract all form field names from a PDF using PyMuPDF."""
    doc = fitz.open(pdf_path)
    fields = {}
    for page in doc:
        widgets = page.widgets()
        for widget in widgets:
            field_name = widget.field_name
            field_type_string = widget.field_type_string
            field_value = widget.field_value
            rect = [widget.rect.x0, widget.rect.y0, widget.rect.x1, widget.rect.y1]
            fields.setdefault(field_name, {
                "type": field_type_string,
                "values": [],  # Handle multiple values if needed
                "rects": []
            })
            fields.get(field_name)["values"].append(field_value)
            fields.get(field_name)["rects"].append(rect)
    doc.close()
    return fields

def fill_pdf_template(template_path, data, output_path):
    """Fill a PDF template with data using PyMuPDF."""
    doc = fitz.open(template_path)
    pdf_fields = get_pdf_fields(template_path)
    print(f"PDF contains these fields: {list(pdf_fields.keys())}")

    for page in doc:
        widgets = page.widgets()
        for widget in widgets:
            field_name = widget.field_name
            value_to_set = None

            if field_name in data:
                value_to_set = data.get(field_name, '')
            elif field_name.lower() in [k.lower() for k in data]:
                for key in data:
                    if key.lower() == field_name.lower():
                        value_to_set = data.get(key, '')
                        break

            if value_to_set is not None:
                try:
                    widget.field_value = value_to_set
                    widget.update()  # Important to update the widget after setting the value
                    print(f"Successfully filled field '{field_name}' with '{value_to_set}'")
                except Exception as e:
                    print(f"Error filling field '{field_name}': {e}")
            else:
                print(f"Warning: Field '{field_name}' not found in the submitted data.")

    doc.save(output_path)
    doc.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inspect_pdf')
def inspect_pdf():
    """Display all form fields in the template PDF."""
    fields = get_pdf_fields(TEMPLATE_PATH)
    return json.dumps(fields, indent=2)

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    # Get form data
    form_data = request.form
    print("Received form data:")
    for key in form_data:
        print(f"  - {key}: {form_data.get(key)}")

    # **IMPORTANT: Map these keys EXACTLY to the field names in your PDF.**
    # Based on your previous output, the PDF field names are:
    # 'text_2hcpn', 'text_3ydqz', 'text_4ybok', 'text_5rysh', 'text_6njmy',
    # 'text_10vfgg', 'text_7wpva', 'text_8uoj', 'text_9quis', 'text_11ikbs'

    data = {
        'text_2hcpn': form_data.get('patient_name', ''),
        'text_3ydqz': form_data.get('test_date', ''),
        'text_4ybok': form_data.get('report_date', ''),
        'text_5rysh': form_data.get('referring_doctor', ''),
        'text_6njmy': form_data.get('patient_name', ''),
        'text_10vfgg': form_data.get('test_date', ''),
        'text_7wpva': form_data.get('patient_age', ''),
        # If you have corresponding form fields for these in your HTML:
        'text_8uoj': form_data.get('referring_doctor', ''), # Replace 'some_other_field_1'
        'text_9quis': form_data.get('report_date', ''), # Replace 'some_other_field_2'
        'text_11ikbs': form_data.get('signing_doctor', ''), # Replace 'some_other_field_3'
    }

    # Create output file
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    output_path = temp_output.name
    temp_output.close()

    print(f"Filling template: {TEMPLATE_PATH}")
    print(f"Saving filled PDF to: {output_path}")

    try:
        # Fill the PDF
        fill_pdf_template(TEMPLATE_PATH, data, output_path)

        # Return the filled PDF
        return send_file(output_path, as_attachment=True, download_name='medical_certificate.pdf')
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return f"Error generating PDF: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)