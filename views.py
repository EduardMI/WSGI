import os
from datetime import datetime

from main import Framework
from patterns.behavioral_patterns import EmailNotifier, SmsNotifier, ListView, CreateView, BaseSerializer
from zde_framework.templator import render
from patterns.creational_patterns import Engine, Logger, MapperRegistry
from patterns.structural_patterns import AppRoute, Debug
from patterns.unit_of_work_pattern import UnitOfWork

site = Engine()
logger = Logger('main')
email_notifier = EmailNotifier()
sms_notifier = SmsNotifier()
UnitOfWork.new_current()
UnitOfWork.get_current().set_mapper_registry(MapperRegistry)

routes = {}


@AppRoute(routes=routes, url='/')
class Index:
    @Debug(name='Index')
    def __call__(self, request):
        return '200 OK', render('index.html', logo=request['project'],
                                objects_list=site.categories)


@AppRoute(routes=routes, url='/contact/')
class Contact:
    @Debug(name='Contact')
    def __call__(self, request):
        if request['method'] == 'POST':
            data = request['data']
            data = Framework.decode_value(data)
            self.write_to_file(data)
            return '200 OK', render('index.html', logo=request['project'])
        return '200 OK', render('contact.html', logo=request['project'])

    @staticmethod
    def write_to_file(data):
        path = 'messages_from_client'
        if not os.path.exists(path):
            os.mkdir(path)
        file_name = f'{path}/{datetime.now().strftime("%d-%m-%Y--%H-%M")}-{data["email"]}.txt'
        with open(f'{file_name}', 'w', encoding='utf-8') as text:
            for key, val in data.items():
                text.write(f'{key}:\n{val}\n\n')


@AppRoute(routes=routes, url='/about/')
class About:
    @Debug(name='About')
    def __call__(self, request):
        return '200 OK', render('about.html', logo=request['project'])


@AppRoute(routes=routes, url='/product-list/')
class ProductsList:
    @Debug(name='ProductList')
    def __call__(self, request):
        logger.log('Список продуктов')
        try:
            category = site.fina_category_by_id(
                int(request['request_params']['id']))
            return '200 Ok', render('product_list.html',
                                    objects_list=category.products,
                                    name=category.name, id=category.id,
                                    logo=request['project'])
        except KeyError:
            return '200 OK', 'No products have been added yet'


@AppRoute(routes=routes, url='/create-product/')
class CreateProduct:
    category_id = -1

    @Debug(name='CreateProduct')
    def __call__(self, request):
        if request['method'] == 'POST':
            data = request['data']
            name = data['name']
            name = site.decode_value(name)
            category = None
            if self.category_id != -1:
                category = site.fina_category_by_id(int(self.category_id))
                product = site.create_product('local', name, category)

                product.observers.append(email_notifier)
                product.observers.append(sms_notifier)

                site.products.append(product)
            return '200 OK', render('product_list.html',
                                    objects_list=category.products,
                                    name=category.name, id=category.id,
                                    logo=request['project'])
        else:
            try:
                self.category_id = int(request['request_params']['id'])
                category = site.fina_category_by_id(int(self.category_id))
                return '200 OK', render('create_product.html', name=category.name,
                                        id=category.id, logo=request['project'])
            except KeyError:
                return '200 OK', 'No categories have been added yet'


@AppRoute(routes=routes, url='/create-category/')
class CreateCategory:
    @Debug(name='CreateCategory')
    def __call__(self, request):
        if request['method'] == 'POST':
            data = request['data']
            name = data['name']
            name = site.decode_value(name)
            category_id = data.get('category_id')
            category = None
            if category_id:
                category = site.fina_category_by_id(int(category_id))
            new_category = site.create_category(name, category)
            site.categories.append(new_category)
            return '200 OK', render('index.html', objects_list=site.categories,
                                    logo=request['project'])
        else:
            categories = site.categories
            return '200 OK', render('create_category.html', categories=categories,
                                    logo=request['project'])


@AppRoute(routes=routes, url='/category-list/')
class CategoryList:
    @Debug(name='CategoryList')
    def __call__(self, request):
        logger.log('Список категорий')
        return '200 OK', render('category_list.html', objects_list=site.categories,
                                logo=request['project'])


@AppRoute(routes=routes, url='/copy-product/')
class CopyProduct:
    @Debug(name='CopyProduct')
    def __call__(self, request):
        request_params = request['request_params']

        try:
            name = request_params['name']
            old_product = site.get_product(name)
            if old_product:
                new_name = f'copy_{name}'
                new_product = old_product.clone()
                new_product.name = new_name
                site.products.append(new_product)
            return '200 OK', render('product_list.html',
                                    objects_list=site.products,
                                    name=new_product.category.name,
                                    logo=request['project'])
        except KeyError:
            return '200 OK', 'No products have been added yet'


@AppRoute(routes=routes, url='/shopuser-list/')
class ShopUserListView(ListView):
    template_name = 'shopuser_list.html'

    def get_queryset(self):
        mapper = MapperRegistry.get_current_mapper('shopuser')
        return mapper.all()


@AppRoute(routes=routes, url='/create-shopuser/')
class ShopUserCreateView(CreateView):
    template_name = 'create_shopuser.html'

    def create_obj(self, data):
        name = data['name']
        name = site.decode_value(name)
        new_obj = site.create_user('shopuser', name)
        site.shopusers.append(new_obj)
        new_obj.mark_new()
        UnitOfWork.get_current().commit()


@AppRoute(routes=routes, url='/add-shopuser/')
class AddShopUserByProductCreateView(CreateView):
    template_name = 'add_shopuser.html'

    def get_context_data(self):
        context = super().get_context_data()
        context['products'] = site.products
        context['shopusers'] = site.shopusers
        return context

    def create_obj(self, data: dict):
        product_name = data['product_name']
        product_name = site.decode_value(product_name)
        product = site.get_product(product_name)
        shopuser_name = data['shopuser_name']
        shopuser_name = site.decode_value(shopuser_name)
        shopuser = site.get_shopuser(shopuser_name)
        product.add_shopuser(shopuser)


@AppRoute(routes=routes, url='/api/')
class ProductApi:
    @Debug(name='ProductApi')
    def __call__(self, request):
        return '200 OK', BaseSerializer(site.products).save()
