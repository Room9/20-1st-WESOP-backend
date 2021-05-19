import json, operator, functools

from django.http      import JsonResponse
from django.views     import View
from django.db.models import Q

from products.models  import Ingredient, Menu, Category, Product, ProductSelection, FeatureCategory

class MetaView(View):
    def get(self, request):
        menus = Menu.objects.all()

        results = [
            {
                "menu_name"     : menu.name,
                "menu_id"       : menu.id,
                "category_list" : [
                    {
                        "category_name"              : category.name,
                        "category_id"                : category.id,
                        "category_description_title" : category.description_title if category.description_title else None,
                        "category_description"       : category.description if category.description else None
                    } for category in menu.category_set.all()
                ]
            } for menu in menus
        ]

        return JsonResponse({'result': results}, status=200)

class ProductListView(View):
    def get(self, request):
        menu_id     = request.GET.get('menu_id', None)
        category_id = request.GET.get('category_id', None)

        skintype_ids       = request.GET.getlist('skintype_id', None)
        productfeature_ids = request.GET.getlist('productfeature_id', None)
        ingredient_ids     = request.GET.getlist('ingredient_id', None)

        q = Q()

        if menu_id and Menu.objects.filter(id=menu_id).exists():
            q = Q(category__menu_id=menu_id)
        elif category_id and Category.objects.filter(id=category_id):
            q = Q(category_id=category_id)
        else:
            return JsonResponse({'MESSAGE':'INVALID_PATH'}, status=404)

        products      = Product.objects.filter(q)
        total_results = []

        if skintype_ids:
            skintype_filter = Q(feature__in=skintype_ids)
            products = products.filter(skintype_filter)

        if productfeature_ids:
            productfeature_filter = Q(feature__in=productfeature_ids)
            products = products.filter(productfeature_filter)

        if ingredient_ids:
            ingredient_filter = Q(ingredient__in=ingredient_ids)
            products = products.filter(ingredient_filter)

        for product in set(products):
            category           = product.category
            menu               = category.menu
            ingredients        = product.ingredient.all()
            product_selections = ProductSelection.objects.filter(product_id=product.id)

            feature_result = [
                {
                    "feature_category_name" : feature_category.name,
                    "features"              : [feature.name for feature in feature_category.feature_set.filter(product=product)]
                } for feature_category in set(FeatureCategory.objects.filter(feature__in=product.feature.all()))
            ]

            results = [
                {
                    "menu_name"                  : menu.name,
                    "menu_id"                    : menu.id,
                    "category_name"              : category.name,
                    "category_id"                : category.id,
                    "category_description_title" : category.description_title,
                    "category_description"       : category.description,
                    "product_name"               : product.name,
                    "product_id"                 : product.id,
                    "product_description"        : product.description,
                    "product_features"           : feature_result,
                    "product_content"            : product.content,
                    "product_content_image_url"  : product.content_image_url,
                    "product_ingredients"        : [ingredient.name for ingredient in ingredients],
                    "product_selections"         : [
                        {
                            "size"      : product_selection.size,
                            "price"     : product_selection.price,
                            "image_url" : product_selection.image_url
                        } for product_selection in product_selections
                    ]
                }
            ]

            total_results.append(results)

        return JsonResponse({'result': total_results}, status=200)

class DetailProductView(View):
    def get(self, request, product_id):
        if not Product.objects.filter(id=product_id).exists():
            return JsonResponse({'MESSAGE':'INVALID_PATH'}, status=404)

        product = Product.objects.get(id=product_id)

        category           = product.category
        menu               = category.menu
        ingredients        = product.ingredient.all()
        product_selections = product.productselection_set.all()
        product.count      += 1
        # product.save() 프로젝트 완성되면 카운트 쌓을 예정입니다 :)

        results = {
                        "menu_name"                 : menu.name,
                        "menu_id"                   : menu.id,
                        "category_name"             : category.name,
                        "category_id"               : category.id,
                        "product_name"              : product.name,
                        "product_id"                : product.id,
                        "product_description"       : product.description,
                        "product_content"           : product.content,
                        "product_content_image_url" : product.content_image_url,
                        "product_ingredients"       : [ingredient.name for ingredient in ingredients],
                        "product_selections"  : [
                            {
                                "size"      : product_selection.size,
                                "price"     : product_selection.price,
                                "image_url" : product_selection.image_url
                            } for product_selection in product_selections
                        ]
        }

        feature_result = [
            {
                "feature_category_name" : feature_category.name,
                "features"              : [feature.name for feature in feature_category.feature_set.filter(product=product)]
            } for feature_category in set(FeatureCategory.objects.filter(feature__in=product.feature.all()))
        ]

        results["product_features"] = feature_result

        return JsonResponse({'result':results}, status=200)
