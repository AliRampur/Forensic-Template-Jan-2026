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
    """Overall inventory metrics and forensic indicators."""
    
    # Basic counts
    total_units = InventoryUnit.objects.count()
    total_properties = Property.objects.count()
    total_commissions = Commission.objects.count()
    
    # Financial metrics
    total_bank_balance = InventoryUnit.objects.aggregate(
        total=Sum('bank_gl_balance')
    )['total'] or 0
    
    total_sales = InventoryUnit.objects.aggregate(
        total=Sum('sale_amount_pre_tax')
    )['total'] or 0
    
    total_commission_amount = Commission.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_rental_income = InventoryUnit.objects.aggregate(
        total=Sum('gl_rental_income')
    )['total'] or 0
    
    # LHS-specific metrics
    lhs_owned = InventoryUnit.objects.filter(current_lhs_property=True).count()
    lhs_rentals = InventoryUnit.objects.filter(is_lhs_rental=True).count()
    
    # Forensic flags
    mco_mismatches = InventoryUnit.objects.filter(mco_not_match=True).count()
    no_mco_available = InventoryUnit.objects.filter(no_mco_available=True).count()
    commission_no_sale = InventoryUnit.objects.filter(commission_but_no_sale=True).count()
    home_sale_entity_mco = InventoryUnit.objects.filter(
        mco_indicates_home_sale_entity=True
    ).count()
    
    # Property breakdown
    property_stats = Property.objects.annotate(
        unit_count=Count('units'),
        total_balance=Sum('units__bank_gl_balance'),
        total_sales=Sum('units__sale_amount_pre_tax'),
        commission_count=Count('units__commissions')
    ).order_by('-unit_count')
    
    # Commission breakdown
    unsupported_commissions = Commission.objects.filter(
        status='UNSUPPORTED'
    ).aggregate(
        count=Count('id'),
        total=Sum('amount')
    )
    
    context = {
        'total_units': total_units,
        'total_properties': total_properties,
        'total_commissions': total_commissions,
        'total_bank_balance': total_bank_balance,
        'total_sales': total_sales,
        'total_commission_amount': total_commission_amount,
        'total_rental_income': total_rental_income,
        'lhs_owned': lhs_owned,
        'lhs_rentals': lhs_rentals,
        'mco_mismatches': mco_mismatches,
        'no_mco_available': no_mco_available,
        'commission_no_sale': commission_no_sale,
        'home_sale_entity_mco': home_sale_entity_mco,
        'property_stats': property_stats,
        'unsupported_commissions_count': unsupported_commissions['count'] or 0,
        'unsupported_commissions_total': unsupported_commissions['total'] or 0,
    }
    
    return render(request, 'forensics/inventory_metrics.html', context)


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

