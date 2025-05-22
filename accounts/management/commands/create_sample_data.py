# accounts/management/commands/create_sample_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from service_requests.models import ServiceCategory, ServiceRequest
from accounts.models import UserProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for testing'

    def handle(self, *args, **options):
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@gasutility.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': UserProfile.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(f'Created admin user: admin/admin123')

        # Create support agent
        agent_user, created = User.objects.get_or_create(
            username='agent1',
            defaults={
                'email': 'agent1@gasutility.com',
                'first_name': 'Support',
                'last_name': 'Agent',
                'role': UserProfile.SUPPORT_AGENT,
                'employee_id': 'EMP001',
                'department': 'Customer Support',
                'is_staff': True,
            }
        )
        if created:
            agent_user.set_password('agent123')
            agent_user.save()
            self.stdout.write(f'Created agent user: agent1/agent123')

        # Create manager
        manager_user, created = User.objects.get_or_create(
            username='manager1',
            defaults={
                'email': 'manager1@gasutility.com',
                'first_name': 'Service',
                'last_name': 'Manager',
                'role': UserProfile.MANAGER,
                'employee_id': 'MGR001',
                'department': 'Customer Service',
                'is_staff': True,
            }
        )
        if created:
            manager_user.set_password('manager123')
            manager_user.save()
            self.stdout.write(f'Created manager user: manager1/manager123')

        # Create sample customers
        for i in range(1, 4):
            customer, created = User.objects.get_or_create(
                username=f'customer{i}',
                defaults={
                    'email': f'customer{i}@example.com',
                    'first_name': f'Customer',
                    'last_name': f'User{i}',
                    'role': UserProfile.CUSTOMER,
                    'customer_id': f'CUST00{i}',
                    'gas_meter_id': f'GM{i:04d}',
                    'service_address': f'{i}23 Main St, City, State 12345',
                    'phone_number': f'555-010{i}',
                }
            )
            if created:
                customer.set_password(f'customer{i}123')
                customer.save()
                self.stdout.write(f'Created customer: customer{i}/customer{i}123')

        # Create service categories
        categories = [
            {
                'name': 'Gas Leak',
                'description': 'Report gas leaks or suspected gas leaks',
                'slug': 'gas-leak'
            },
            {
                'name': 'Service Connection',
                'description': 'New service connections and disconnections',
                'slug': 'service-connection'
            },
            {
                'name': 'Billing Inquiry',
                'description': 'Questions about gas bills and payments',
                'slug': 'billing-inquiry'
            },
            {
                'name': 'Meter Reading',
                'description': 'Issues with meter readings or meter access',
                'slug': 'meter-reading'
            },
            {
                'name': 'Emergency Service',
                'description': 'Emergency gas-related issues',
                'slug': 'emergency-service'
            },
            {
                'name': 'Maintenance',
                'description': 'Scheduled maintenance and repairs',
                'slug': 'maintenance'
            }
        ]

        for cat_data in categories:
            category, created = ServiceCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create sample service requests
        customers = User.objects.filter(role=UserProfile.CUSTOMER)
        categories = ServiceCategory.objects.all()
        
        sample_requests = [
            {
                'title': 'Suspected gas leak in basement',
                'description': 'I smell gas in my basement near the water heater. Please send someone urgently.',
                'priority': ServiceRequest.URGENT,
                'category': categories.get(slug='gas-leak'),
                'customer': customers.first(),
            },
            {
                'title': 'High gas bill inquiry',
                'description': 'My gas bill this month is much higher than usual. Can you help me understand why?',
                'priority': ServiceRequest.MEDIUM,
                'category': categories.get(slug='billing-inquiry'),
                'customer': customers.first(),
            },
            {
                'title': 'Request new service connection',
                'description': 'I need gas service connected to my new home at 456 Oak Street.',
                'priority': ServiceRequest.LOW,
                'category': categories.get(slug='service-connection'),
                'customer': customers.last(),
            },
        ]

        for req_data in sample_requests:
            ServiceRequest.objects.get_or_create(
                title=req_data['title'],
                customer=req_data['customer'],
                defaults=req_data
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )