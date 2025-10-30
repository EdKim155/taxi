import os
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import qrcode
from io import BytesIO
import pytz
import config


class PDFService:
    def __init__(self):
        self.template_dir = config.TEMPLATES_DIR
        self.output_dir = config.WAYBILLS_DIR
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_qr_code(self, data: str) -> str:
        """Generate QR code and return as base64 string."""
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode()
    
    def format_datetime(self, dt: datetime, fmt: str = "%d.%m.%Y %H:%M") -> str:
        """Format datetime to string."""
        return dt.strftime(fmt)
    
    def generate_waybill_pdf(
        self,
        waybill_data: Dict[str, Any],
        driver_data: Dict[str, Any],
        settings: Dict[str, Any]
    ) -> tuple[str, str]:
        """
        Generate waybill PDF.
        
        Returns:
            tuple: (pdf_filename, pdf_filepath)
        """
        # Get timezone
        tz_name = driver_data.get('tz', settings.get('tz_default', 'Europe/Moscow'))
        tz = pytz.timezone(tz_name)
        
        # Calculate times
        dt_fact = datetime.now(tz)
        time_shift = settings.get('time_shift_minutes', 60)
        dt_print = dt_fact - timedelta(minutes=time_shift)
        
        # Get waybill number
        wb_number = waybill_data.get('wb_number', 'N/A')
        
        # Calculate effective odometer
        odo_input = waybill_data.get('odo_input', 0)
        odo_delta = driver_data.get('odo_delta', 0)
        
        if settings.get('apply_odo_delta', True):
            odo_effective = max(0, odo_input - odo_delta)
        else:
            odo_effective = odo_input
        
        # Generate QR code
        qr_data = f"WB:{wb_number}|DT:{dt_print.isoformat()}|ODO:{odo_effective}"
        qr_code_base64 = self.generate_qr_code(qr_data)
        
        # Prepare template context
        context = {
            'wb_number': wb_number,
            'dt_fact_formatted': self.format_datetime(dt_fact),
            'dt_print_formatted': self.format_datetime(dt_print, "%d.%m.%Y"),
            'dt_print_time': self.format_datetime(dt_print, "%H:%M"),
            'org_name': driver_data.get('org_name', 'Не указано'),
            'driver_id': driver_data.get('driver_id', 'N/A'),
            'driver_fio': driver_data.get('fio', 'N/A'),
            'driver_phone': driver_data.get('phone', 'N/A'),
            'car_model': driver_data.get('car_model', 'N/A'),
            'car_plate': driver_data.get('car_plate', 'N/A'),
            'vin': driver_data.get('vin', ''),
            'med_worker': driver_data.get('med_worker', 'Медработник'),
            'mech_worker': driver_data.get('mech_worker', 'Механик'),
            'odo_input': odo_input,
            'odo_delta': odo_delta,
            'odo_effective': odo_effective,
            'qr_code_data': qr_code_base64
        }
        
        # Render HTML template
        template = self.env.get_template('waybill.html')
        html_content = template.render(context)
        
        # Generate PDF
        pdf_filename = f"waybill_{wb_number.replace('-', '_')}_{dt_fact.strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_filepath = os.path.join(self.output_dir, pdf_filename)
        
        HTML(string=html_content).write_pdf(pdf_filepath)
        
        return pdf_filename, pdf_filepath
