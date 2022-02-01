from views import Index, Contact, About, ProductsList, CreateProduct, CopyProduct, CreateCategory, CategoryList


def secret_front(request):
    request['project'] = 'ZDE FRAMEWORK'


def other_front(request):
    request['key'] = 'key'


fronts = [secret_front, other_front]


# urlpatterns = {
#     '/': Index(),
#     '/about/': About(),
#     '/contact/': Contact(),
#
#     '/product-list/': ProductsList(),
#     '/create-product/': CreateProduct(),
#     '/copy-product/': CopyProduct(),
#
#     '/category-list/': CategoryList(),
#     '/create-category/': CreateCategory()
# }
