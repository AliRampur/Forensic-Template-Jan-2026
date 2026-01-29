"""
Views for TraceFlow Forensic Accounting System
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.db.models import Sum, Count, Avg, Q
import plotly.graph_objects as go

from .inventory_models import Property, InventoryUnit, Commission


def home_view(request):
    """Dashboard home view with summary statistics."""
    context = {
        'total_properties': Property.objects.count(),
        'total_units': InventoryUnit.objects.count(),
        'total_commissions': Commission.objects.count(),
        'lhs_owned': InventoryUnit.objects.filter(current_lhs_property=True).count(),
        'lhs_rentals': InventoryUnit.objects.filter(is_lhs_rental=True).count(),
    }
    return render(request, 'forensics/dashboard.html', context)


def api_docs_view(request):
    """API documentation view."""
    return render(request, 'forensics/api_docs.html')


def resume_view(request):
    """Public resume page featuring the expert."""
    context = {
        'expert_name': 'Ali Rampurawala',
        'expert_title': 'Financial Forensics Expert',
        'linkedin_url': 'https://www.linkedin.com/in/ali-rampurawala-8bbb118/',
    }
    return render(request, 'forensics/resume.html', context)


def sankey_view(request):
    """
    Money Flow Visualization for LHS Inventory
    
    Traces money from Sales Revenue through Commissions and Expenses,
    highlighting suspicious patterns in red.
    
    Visual Strategy:
    - Green flows: Sales revenue from properties
    - Blue flows: Legitimate expenses (supported commissions)
    - Red flows: Unsupported commissions or flagged transactions
    - Yellow flows: Rental income
    """
    sources = []
    targets = []
    values = []
    colors = []
    label_list = []
    
    def get_index(label):
        """Helper to map text labels to integer indices required by Plotly."""
        if label not in label_list:
            label_list.append(label)
        return label_list.index(label)
    
    # Get units with sales data
    units_with_sales = InventoryUnit.objects.filter(
        sale_amount_pre_tax__isnull=False,
        sale_amount_pre_tax__gt=0
    ).select_related('property')
    
    # Add sales flows from each property to "Total Sales Revenue"
    property_sales = {}
    for unit in units_with_sales:
        prop_name = unit.property.short_name
        if prop_name not in property_sales:
            property_sales[prop_name] = 0
        property_sales[prop_name] += float(unit.sale_amount_pre_tax)
    
    for prop_name, total_sales in property_sales.items():
        sources.append(get_index(prop_name))
        targets.append(get_index("Total Sales Revenue"))
        values.append(total_sales)
        colors.append("rgba(0, 128, 0, 0.5)")  # Green for sales
    
    # Add rental income flows
    units_with_rental = InventoryUnit.objects.filter(
        gl_rental_income__isnull=False,
        gl_rental_income__gt=0
    ).select_related('property')
    
    property_rental = {}
    for unit in units_with_rental:
        prop_name = unit.property.short_name
        if prop_name not in property_rental:
            property_rental[prop_name] = 0
        property_rental[prop_name] += float(unit.gl_rental_income)
    
    for prop_name, total_rental in property_rental.items():
        sources.append(get_index(prop_name))
        targets.append(get_index("Rental Income"))
        values.append(total_rental)
        colors.append("rgba(255, 193, 7, 0.5)")  # Yellow for rentals
    
    # Add commission flows
    commissions = Commission.objects.select_related('unit', 'unit__property').all()
    
    # Group commissions by recipient and status
    for commission in commissions:
        source_label = "Total Sales Revenue"
        target_label = f"Commission: {commission.recipient}"
        amount = float(commission.amount)
        
        sources.append(get_index(source_label))
        targets.append(get_index(target_label))
        values.append(amount)
        
        # Color by support status
        if commission.status == 'UNSUPPORTED':
            colors.append("rgba(220, 53, 69, 0.6)")  # Red for unsupported
        elif commission.status == 'INSUFFICIENT':
            colors.append("rgba(255, 193, 7, 0.6)")  # Yellow for insufficient
        else:
            colors.append("rgba(13, 110, 253, 0.5)")  # Blue for supported
    
    # Create the Plotly Figure
    if not sources:  # Handle empty data case
        fig = go.Figure()
        fig.add_annotation(
            text="No sales or commission data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
    else:
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=label_list,
                color="lightblue"
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=colors
            )
        )])
    
    fig.update_layout(
        title="LHS Inventory Money Flow - Sales, Rentals & Commissions",
        font=dict(size=12),
        height=800
    )
    
    # Convert to JSON for embedding in Django Template
    graph_json = fig.to_json()
    
    return render(request, 'forensics/sankey.html', {'graph_json': graph_json})


# Old Account/Transaction/ReconciliationMatch list views removed


# Inventory Views
def inventory_metrics_view(request):
    """Overall inventory metrics showing units by property with filtering."""
    
    # Basic counts
    total_units = InventoryUnit.objects.count()
    total_properties = Property.objects.count()
    
    # Property breakdown with unique base_unit counts
    property_stats = []
    for property_obj in Property.objects.all().order_by('short_name'):
        unique_base_units = InventoryUnit.objects.filter(
            property=property_obj
        ).values('base_unit').distinct().count()
        
        property_stats.append({
            'property': property_obj,
            'unit_count': unique_base_units
        })
    
    # Handle filtering
    queryset = InventoryUnit.objects.all().select_related('property')
    
    # Get filter parameters
    base_property = request.GET.get('base_property')
    unit_lot = request.GET.get('unit_lot')
    lhs_property = request.GET.get('lhs_property')
    builder = request.GET.get('builder')
    mco_owner = request.GET.get('mco_owner')
    serial_number = request.GET.get('serial_number')
    
    # Apply filters
    if base_property:
        queryset = queryset.filter(property_id=base_property)
    
    if unit_lot:
        queryset = queryset.filter(
            Q(unit_number__icontains=unit_lot) |
            Q(property_unit__icontains=unit_lot) |
            Q(base_unit__icontains=unit_lot)
        )
    
    if lhs_property:
        queryset = queryset.filter(current_lhs_property=True)
    
    if builder:
        queryset = queryset.filter(builder__icontains=builder)
    
    if mco_owner:
        queryset = queryset.filter(mco_owner__icontains=mco_owner)
    
    if serial_number:
        queryset = queryset.filter(serial_number__icontains=serial_number)
    
    # Order results
    filtered_units = queryset.order_by('property', 'unit_number')
    
    # Get unique values for dropdowns
    properties = Property.objects.all().order_by('short_name')
    builders = InventoryUnit.objects.exclude(builder='').values_list('builder', flat=True).distinct().order_by('builder')
    mco_owners = InventoryUnit.objects.exclude(mco_owner='').values_list('mco_owner', flat=True).distinct().order_by('mco_owner')
    
    # Determine if filters are active
    filters_active = any([base_property, unit_lot, lhs_property, builder, mco_owner, serial_number])
    
    context = {
        'total_units': total_units,
        'total_properties': total_properties,
        'property_stats': property_stats,
        'filtered_units': filtered_units if filters_active else None,
        'filters_active': filters_active,
        'properties': properties,
        'builders': builders,
        'mco_owners': mco_owners,
        # Filter values for preserving state
        'selected_base_property': base_property or '',
        'selected_unit_lot': unit_lot or '',
        'selected_lhs_property': lhs_property or '',
        'selected_builder': builder or '',
        'selected_mco_owner': mco_owner or '',
        'selected_serial_number': serial_number or '',
    }
    
    return render(request, 'forensics/inventory_metrics.html', context)


def inventory_unit_detail_view(request, pk):
    """Detail view for a specific inventory unit."""
    from django.shortcuts import get_object_or_404
    
    unit = get_object_or_404(InventoryUnit.objects.select_related('property'), pk=pk)
    commissions = unit.commissions.all()
    
    context = {
        'unit': unit,
        'commissions': commissions,
    }
    
    return render(request, 'forensics/inventory_unit_detail.html', context)


def document_inventory_view(request):
    """Document inventory and retrieval page."""
    from django.db.models import Q
    from .inventory_models import Document
    
    # Get filter parameters
    doc_type = request.GET.get('doc_type', '')
    property_id = request.GET.get('property', '')
    
    # Get all properties
    properties = Property.objects.all().order_by('short_name')
    
    # Initialize queryset
    documents = Document.objects.all().select_related('property')
    
    # Apply document type filter
    if doc_type:
        documents = documents.filter(document_type=doc_type)
    
    # Apply property filter
    if property_id:
        documents = documents.filter(property_id=property_id)
    
    # Apply additional filters based on document type
    if doc_type == 'TAX':
        tax_year = request.GET.get('tax_year')
        if tax_year:
            documents = documents.filter(tax_year=tax_year)
        
        # Get unique tax years for the dropdown
        tax_years = sorted(
            set(Document.objects.filter(document_type='TAX')
                .exclude(tax_year__isnull=True)
                .values_list('tax_year', flat=True)),
            reverse=True
        )
        context_extra = {'tax_years': tax_years}
    
    elif doc_type == 'BANK':
        bank_year = request.GET.get('bank_year')
        bank_month = request.GET.get('bank_month')
        bank_name = request.GET.get('bank_name')
        
        if bank_year:
            documents = documents.filter(statement_year=bank_year)
        if bank_month:
            documents = documents.filter(statement_month=bank_month)
        if bank_name:
            documents = documents.filter(bank_name__icontains=bank_name)
        
        bank_years = sorted(
            set(Document.objects.filter(document_type='BANK')
                .exclude(statement_year__isnull=True)
                .values_list('statement_year', flat=True)),
            reverse=True
        )
        bank_names = Document.objects.filter(document_type='BANK').exclude(bank_name='').values_list('bank_name', flat=True).distinct().order_by('bank_name')
        
        context_extra = {
            'bank_years': bank_years,
            'bank_names': bank_names,
            'months': [(i, f"{i:02d} - {'January,February,March,April,May,June,July,August,September,October,November,December'.split(',')[i-1]}") for i in range(1, 13)],
        }
    
    elif doc_type == 'INVOICE':
        invoice_year = request.GET.get('invoice_year')
        vendor_name = request.GET.get('vendor_name')
        
        if invoice_year:
            documents = documents.filter(invoice_year=invoice_year)
        if vendor_name:
            documents = documents.filter(vendor_name__icontains=vendor_name)
        
        invoice_years = sorted(
            set(Document.objects.filter(document_type='INVOICE')
                .exclude(invoice_year__isnull=True)
                .values_list('invoice_year', flat=True)),
            reverse=True
        )
        vendors = Document.objects.filter(document_type='INVOICE').exclude(vendor_name='').values_list('vendor_name', flat=True).distinct().order_by('vendor_name')
        
        context_extra = {
            'invoice_years': invoice_years,
            'vendors': vendors,
        }
    else:
        context_extra = {}
    
    # Determine if filters are active
    filters_active = bool(doc_type)
    
    context = {
        'doc_type': doc_type,
        'properties': properties,
        'documents': documents if filters_active else None,
        'filters_active': filters_active,
        'doc_types': Document.DOC_TYPE_CHOICES,
        'selected_property': property_id or '',
        **context_extra,
    }
    
    return render(request, 'forensics/document_inventory.html', context)


class InventoryUnitListView(ListView):
    """List all inventory units with filtering."""
    model = InventoryUnit
    template_name = 'forensics/inventory_unit_list.html'
    context_object_name = 'units'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('property')
        
        # Filter by property
        property_id = self.request.GET.get('property')
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        
        # Filter by LHS ownership
        lhs_owned = self.request.GET.get('lhs_owned')
        if lhs_owned:
            queryset = queryset.filter(current_lhs_property=True)
        
        # Filter by rental status
        is_rental = self.request.GET.get('is_rental')
        if is_rental:
            queryset = queryset.filter(is_lhs_rental=True)
        
        # Filter by forensic flags
        show_issues = self.request.GET.get('show_issues')
        if show_issues:
            queryset = queryset.filter(
                Q(mco_not_match=True) |
                Q(no_mco_available=True) |
                Q(commission_but_no_sale=True) |
                Q(mco_indicates_home_sale_entity=True)
            )
        
        return queryset.order_by('property', 'unit_number')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['properties'] = Property.objects.all()
        context['selected_property'] = self.request.GET.get('property', '')
        context['lhs_owned'] = self.request.GET.get('lhs_owned', '')
        context['is_rental'] = self.request.GET.get('is_rental', '')
        context['show_issues'] = self.request.GET.get('show_issues', '')
        return context


class CommissionListView(ListView):
    """List all commissions with filtering."""
    model = Commission
    template_name = 'forensics/commission_list.html'
    context_object_name = 'commissions'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('unit', 'unit__property')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by recipient
        recipient = self.request.GET.get('recipient')
        if recipient:
            queryset = queryset.filter(recipient__icontains=recipient)
        
        # Filter by property
        property_id = self.request.GET.get('property')
        if property_id:
            queryset = queryset.filter(unit__property_id=property_id)
        
        return queryset.order_by('-amount')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['properties'] = Property.objects.all()
        context['statuses'] = Commission._meta.get_field('status').choices
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_property'] = self.request.GET.get('property', '')
        context['selected_recipient'] = self.request.GET.get('recipient', '')
        
        # Summary stats
        queryset = self.get_queryset()
        context['total_amount'] = queryset.aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_count'] = queryset.count()
        
        return context

