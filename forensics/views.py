"""
Views for TraceFlow Forensic Accounting System
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
import plotly.graph_objects as go

from .models import Account, Transaction, ReconciliationMatch


def home_view(request):
    """Dashboard home view with summary statistics."""
    context = {
        'total_accounts': Account.objects.count(),
        'total_transactions': Transaction.objects.count(),
        'total_matches': ReconciliationMatch.objects.count(),
        'bank_accounts': Account.objects.filter(is_internal_book=False).count(),
        'book_accounts': Account.objects.filter(is_internal_book=True).count(),
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
    Courtroom-Ready Sankey Visualization
    
    Traces money from Source (Verified Income) to Destination (Verified Spend),
    highlighting "Unverified" funds in bright red.
    
    Visual Strategy:
    - Green Nodes: Verified Sources (Customers, Loans)
    - Grey Nodes: Internal Transfers
    - Red Nodes: Unverified/Suspicious outflows
    """
    matches = ReconciliationMatch.objects.all().select_related(
        'bank_transaction',
        'book_entry'
    )
    
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
    
    for match in matches:
        # Source: Where money came from (Description)
        src_label = match.bank_transaction.description[:30]  # Truncate for readability
        # Target: The Account it went into (or Category)
        tgt_label = "Verified Assets"
        
        sources.append(get_index(src_label))
        targets.append(get_index(tgt_label))
        values.append(float(abs(match.bank_transaction.amount)))
        
        # Color logic: Red if unverified/manual, Grey otherwise
        if match.match_type == 'MANUAL':
            colors.append("rgba(255, 0, 0, 0.6)")  # Red link
        elif match.match_type == 'EXACT':
            colors.append("rgba(0, 128, 0, 0.6)")  # Green link
        else:
            colors.append("rgba(100, 100, 100, 0.4)")  # Grey link
    
    # Create the Plotly Figure
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=label_list,
            color="blue"
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=colors
        )
    )])
    
    fig.update_layout(
        title="Transaction Flow Analysis - Forensic Reconciliation",
        font=dict(size=12)
    )
    
    # Convert to JSON for embedding in Django Template
    graph_json = fig.to_json()
    
    return render(request, 'forensics/sankey.html', {'graph_json': graph_json})


class AccountListView(ListView):
    """List all accounts with transaction summaries."""
    model = Account
    template_name = 'forensics/account_list.html'
    context_object_name = 'accounts'
    paginate_by = 20


class TransactionListView(ListView):
    """List all transactions with filtering options."""
    model = Transaction
    template_name = 'forensics/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('account')
        account_id = self.request.GET.get('account')
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        return queryset


class ReconciliationMatchListView(ListView):
    """List all reconciliation matches."""
    model = ReconciliationMatch
    template_name = 'forensics/match_list.html'
    context_object_name = 'matches'
    paginate_by = 50
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'bank_transaction',
            'book_entry',
            'bank_transaction__account',
            'book_entry__account'
        )
