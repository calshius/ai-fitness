import logging
import json
import aiohttp
from typing import List, Dict, Any
from ..scrapers.base_scraper import BaseScraper

logger = logging.getLogger("ai_fitness_api")


class TescoScraper(BaseScraper):
    """Scraper for Tesco supermarket"""

    def __init__(self):
        super().__init__()
        self.api_url = "https://api.tesco.com/shoppingexperience"

    async def search_product(self, product_name: str) -> List[Dict[str, Any]]:
        """Search for a product in Tesco"""
        logger.info(f"Searching for {product_name} in Tesco")

        # Construct the GraphQL query payload as shown in the test-tesco.sh script
        payload = [
            {
                "operationName": "Search",
                "variables": {
                    "page": 1,
                    "includeRestrictions": True,
                    "includeVariations": True,
                    "showStarRating": True,
                    "showDepositReturnCharge": False,
                    "showPopularFilter": True,
                    "query": product_name,
                    "count": 24,
                    "configs": [
                        {
                            "featureKey": "dynamic_filter",
                            "params": [{"name": "enable", "value": "false"}],
                        }
                    ],
                    "filterCriteria": [{"name": "inputType", "values": ["suggested"]}],
                    "appliedFacetArgs": [],
                    "sortBy": "relevance",
                },
                "extensions": {"mfeName": "unknown"},
                # Use the exact query from the test-tesco.sh script
                "query": """query Search($query: String!, $page: Int = 1, $count: Int, $sortBy: String, $offset: Int, $facet: ID, $favourites: Boolean, $filterCriteria: [filterCriteria], $configs: [ConfigArgType], $includeRestrictions: Boolean = true, $includeVariations: Boolean = true, $mediaExperiments: BrowseSearchConfig, $showStarRating: Boolean = true, $showDepositReturnCharge: Boolean = false, $showPopularFilter: Boolean = true, $appliedFacetArgs: [AppliedFacetArgs]) {
  search(
    query: $query
    page: $page
    count: $count
    sortBy: $sortBy
    offset: $offset
    facet: $facet
    favourites: $favourites
    filterCriteria: $filterCriteria
    configs: $configs
    config: $mediaExperiments
    appliedFacetArgs: $appliedFacetArgs
  ) {
    pageInformation: info {
      ...PageInformation
      __typename
    }
    results {
      node {
        ... on MPProduct {
          ...ProductItem
          __typename
        }
        ... on FNFProduct {
          ...ProductItem
          __typename
        }
        ... on ProductType {
          ...ProductItem
          __typename
        }
        __typename
      }
      __typename
    }
    facetLists: facetGroups {
      ...FacetLists
      __typename
    }
    popularFilters: popFilters @include(if: $showPopularFilter) {
      ...PopFilters
      __typename
    }
    facets {
      ...facet
      __typename
    }
    options {
      sortBy
      __typename
    }
    __typename
  }
}

fragment ProductItem on ProductInterface {
  typename: __typename
  ... on ProductType {
    context {
      type
      ... on ProductContextOfferType {
        linkTo
        offerType
        __typename
      }
      __typename
    }
    __typename
  }
  ... on MPProduct {
    context {
      type
      ... on ProductContextOfferType {
        linkTo
        offerType
        __typename
      }
      __typename
    }
    seller {
      id
      name
      __typename
    }
    fulfilment(deliveryOptions: BEST) {
      __typename
      ... on ProductDeliveryType {
        maxDeliveryDays
        charges {
          value
          __typename
        }
        __typename
      }
    }
    variations {
      ...Variation @include(if: $includeVariations)
      __typename
    }
    __typename
  }
  ... on FNFProduct {
    context {
      type
      ... on ProductContextOfferType {
        linkTo
        offerType
        __typename
      }
      __typename
    }
    variations {
      ...Variation @include(if: $includeVariations)
      __typename
    }
    __typename
  }
  id
  tpnb
  tpnc
  gtin
  adId
  baseProductId
  title
  brandName
  shortDescription
  defaultImageUrl
  superDepartmentId
  media {
    defaultImage {
      aspectRatio
      __typename
    }
    __typename
  }
  quantityInBasket
  superDepartmentName
  departmentId
  departmentName
  aisleId
  aisleName
  shelfId
  shelfName
  displayType
  productType
  charges @include(if: $showDepositReturnCharge) {
    ... on ProductDepositReturnCharge {
      __typename
      amount
    }
    __typename
  }
  averageWeight
  bulkBuyLimit
  maxQuantityAllowed: bulkBuyLimit
  groupBulkBuyLimit
  bulkBuyLimitMessage
  bulkBuyLimitGroupId
  timeRestrictedDelivery
  restrictedDelivery
  isForSale
  isInFavourites
  isNew
  isRestrictedOrderAmendment
  status
  maxWeight
  minWeight
  increment
  details {
    components {
      ...Competitors
      ...AdditionalInfo
      __typename
    }
    __typename
  }
  catchWeightList {
    price
    weight
    default
    __typename
  }
  price {
    price: actual
    unitPrice
    unitOfMeasure
    actual
    __typename
  }
  promotions {
    id
    promotionType
    startDate
    endDate
    description
    unitSellingInfo
    price {
      beforeDiscount
      afterDiscount
      __typename
    }
    attributes
    __typename
  }
  restrictions @include(if: $includeRestrictions) {
    type
    isViolated
    message
    __typename
  }
  reviews @include(if: $showStarRating) {
    stats {
      noOfReviews
      overallRating
      overallRatingRange
      __typename
    }
    __typename
  }
  modelMetadata {
    name
    version
    __typename
  }
}

fragment Competitors on CompetitorsInfo {
  competitors {
    id
    priceMatch {
      isMatching
      __typename
    }
    __typename
  }
  __typename
}

fragment AdditionalInfo on AdditionalInfo {
  isLowEverydayPricing
  __typename
}

fragment Variation on VariationsType {
  products {
    id
    baseProductId
    variationAttributes {
      attributeGroup
      attributeGroupData {
        name
        value
        attributes {
          name
          value
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}

fragment FacetLists on ProductListFacetsType {
  __typename
  category
  categoryId
  facets {
    facetId: id
    facetName: name
    binCount: count
    isSelected: selected
    __typename
  }
}

fragment PageInformation on ListInfoType {
  totalCount: total
  pageNo: page
  pageId
  count
  pageSize
  matchType
  offset
  query {
    searchTerm
    actualTerm
    __typename
  }
  __typename
}

fragment PopFilters on ProductListFacetsType {
  category
  categoryId
  facets {
    facetId: id
    facetName: name
    binCount: count
    isSelected: selected
    __typename
  }
  __typename
}

fragment facet on FacetInterface {
  __typename
  id
  name
  type
  ... on FacetListType {
    id
    name
    listValues: values {
      name
      value
      isSelected
      count
      __typename
    }
    multiplicity
    metadata {
      description
      footerText
      linkText
      linkUrl
      __typename
    }
    __typename
  }
  ... on FacetMultiLevelType {
    id
    name
    multiLevelValues: values {
      children {
        count
        name
        value
        isSelected
        __typename
      }
      appliedValues {
        isSelected
        name
        value
        __typename
      }
      __typename
    }
    multiplicity
    metadata {
      description
      footerText
      linkText
      linkUrl
      __typename
    }
    __typename
  }
  ... on FacetRangeType {
    rangeValues: values {
      appliedMax
      appliedMin
      stepper
      min
      max
      __typename
    }
    __typename
  }
  ... on FacetBooleanType {
    booleanValues: values {
      count
      isSelected
      value
      name
      __typename
    }
    __typename
  }
}""",
            }
        ]

        headers = {
            "Connection": "keep-alive",
            "Origin": "https://www.tesco.com",
            "Referer": "https://www.tesco.com/",
            "accept": "application/json",
            "accept-language": "en-GB",
            "content-type": "application/json",
            "language": "en-GB",
            "region": "UK",
            "x-apikey": "TvOSZJHlEk0pjniDGQFAc9Q59WGAR4dA",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url, json=payload, headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_results(data)
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Error searching Tesco: {response.status}, {error_text}"
                        )
                        return []
        except Exception as e:
            logger.error(f"Error searching Tesco: {str(e)}")
            return []

    def _parse_results(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse the results from the Tesco API"""
        results = []

        try:
            # Check if there are errors in the response
            if data and isinstance(data, list) and len(data) > 0:
                if "errors" in data[0]:
                    logger.error(f"API returned errors: {data}")
                    return []

                search_data = data[0].get("data", {}).get("search", {})

                # Extract products from the response
                product_results = search_data.get("results", [])

                logger.info(f"Found {len(product_results)} products in Tesco response")

                for product_result in product_results:
                    try:
                        product = product_result.get("node", {})

                        # Extract product details
                        product_id = product.get("id", "")
                        title = product.get("title", "")
                        image_url = product.get("defaultImageUrl", "")

                        # Extract price information
                        price_info = product.get("price", {})
                        price = price_info.get("price", 0.0)
                        unit_price = price_info.get("unitPrice", 0.0)
                        unit_measure = price_info.get("unitOfMeasure", "")

                        # Construct the product URL
                        url = f"https://www.tesco.com/groceries/en-GB/products/{product_id}"

                        product_data = {
                            "name": title,
                            "price": price,
                            "unit_price": f"{unit_price} per {unit_measure}"
                            if unit_price and unit_measure
                            else "",
                            "url": url,
                            "image_url": image_url,
                        }

                        results.append(self._format_result(product_data))
                    except Exception as e:
                        logger.error(f"Error parsing product: {str(e)}")
                        continue
            else:
                logger.warning("Unexpected response format from Tesco API")

        except Exception as e:
            logger.error(f"Error parsing Tesco results: {str(e)}")

        return results
