"""
Utilidades para generación de PDFs reutilizables
Reduce duplicación de código en exportación a PDF
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO


class EstilosPDF:
    """
    Clase para centralizar estilos comunes de PDF.
    Evita duplicación de configuración de estilos.
    """
    
    @staticmethod
    def obtener_estilos_base():
        """Retorna los estilos base de reportlab"""
        return getSampleStyleSheet()
    
    @staticmethod
    def estilo_titulo(base_styles):
        """Estilo para títulos principales"""
        return ParagraphStyle(
            'CustomTitle',
            parent=base_styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
    
    @staticmethod
    def estilo_subtitulo(base_styles):
        """Estilo para subtítulos"""
        return ParagraphStyle(
            'Subtitle',
            parent=base_styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
    
    @staticmethod
    def estilo_seccion(base_styles):
        """Estilo para encabezados de sección"""
        return ParagraphStyle(
            'Section',
            parent=base_styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=6
        )
    
    @staticmethod
    def estilo_derecha(base_styles):
        """Estilo para texto alineado a la derecha"""
        return ParagraphStyle(
            'Right',
            parent=base_styles['Normal'],
            alignment=TA_RIGHT
        )


class GeneradorPDF:
    """
    Clase base para generar PDFs con configuración común.
    Implementa el patrón Template Method.
    """
    
    def __init__(self, titulo, orientacion='portrait'):
        """
        Args:
            titulo: Título del documento
            orientacion: 'portrait' o 'landscape'
        """
        self.titulo = titulo
        self.orientacion = orientacion
        self.buffer = BytesIO()
        self.elements = []
        self.styles = EstilosPDF.obtener_estilos_base()
        
        # Crear estilos personalizados
        self.title_style = EstilosPDF.estilo_titulo(self.styles)
        self.subtitle_style = EstilosPDF.estilo_subtitulo(self.styles)
        self.section_style = EstilosPDF.estilo_seccion(self.styles)
        self.right_style = EstilosPDF.estilo_derecha(self.styles)
    
    def _configurar_documento(self):
        """Configura el documento PDF con los parámetros base"""
        pagesize = landscape(letter) if self.orientacion == 'landscape' else letter
        return SimpleDocTemplate(
            self.buffer,
            pagesize=pagesize,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            rightMargin=0.6*inch,
            leftMargin=0.6*inch
        )
    
    def agregar_encabezado(self, empresa, titulo_reporte, periodo=""):
        """
        Agrega un encabezado estándar al PDF.
        
        Args:
            empresa: Objeto Empresa
            titulo_reporte: Título del reporte
            periodo: Texto del período (opcional)
        """
        self.elements.append(Paragraph(f"<b>{empresa.nombre}</b>", self.title_style))
        self.elements.append(Paragraph(titulo_reporte, self.title_style))
        
        if periodo:
            self.elements.append(Paragraph(periodo, self.subtitle_style))
        
        self.elements.append(Spacer(1, 0.2*inch))
    
    def agregar_tabla(self, datos, anchos_columnas, estilo_tabla=None):
        """
        Agrega una tabla al PDF con estilo estándar.
        
        Args:
            datos: Lista de listas con los datos de la tabla
            anchos_columnas: Lista con anchos de columnas
            estilo_tabla: TableStyle personalizado (opcional)
        """
        tabla = Table(datos, colWidths=anchos_columnas)
        
        if not estilo_tabla:
            estilo_tabla = self._estilo_tabla_estandar()
        
        tabla.setStyle(estilo_tabla)
        self.elements.append(tabla)
    
    def _estilo_tabla_estandar(self):
        """Retorna un estilo de tabla estándar"""
        return TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Contenido
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
            
            # Totales (última fila)
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            ('TOPPADDING', (0, -1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
        ])
    
    def agregar_espaciador(self, altura=0.2):
        """Agrega un espaciador vertical"""
        self.elements.append(Spacer(1, altura*inch))
    
    def generar_periodo_texto(self, fecha_inicio, fecha_fin):
        """
        Genera texto de período para mostrar en reportes.
        
        Args:
            fecha_inicio: Fecha de inicio (datetime.date o None)
            fecha_fin: Fecha de fin (datetime.date o None)
        
        Returns:
            String con el texto del período
        """
        if fecha_inicio and fecha_fin:
            return f"Del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"
        elif fecha_inicio:
            return f"Desde {fecha_inicio.strftime('%d/%m/%Y')}"
        elif fecha_fin:
            return f"Hasta {fecha_fin.strftime('%d/%m/%Y')}"
        else:
            return "Todos los períodos"
    
    def construir(self):
        """
        Construye el PDF y retorna el buffer.
        
        Returns:
            BytesIO buffer con el PDF generado
        """
        doc = self._configurar_documento()
        doc.build(self.elements)
        self.buffer.seek(0)
        return self.buffer


def formatear_moneda(valor):
    """
    Formatea un valor numérico como moneda.
    
    Args:
        valor: Número (int, float, Decimal)
    
    Returns:
        String formateado como moneda
    """
    return f"${float(valor):,.2f}"


def crear_fila_totales(labels, valores):
    """
    Crea una fila de totales para tablas.
    
    Args:
        labels: Lista de labels (uno vacío, uno con 'TOTALES', etc.)
        valores: Lista de valores a formatear como moneda
    
    Returns:
        Lista con la fila formateada
    """
    fila = []
    for i, label in enumerate(labels):
        if label:
            fila.append(label)
        else:
            fila.append(formatear_moneda(valores[i]))
    
    return fila

