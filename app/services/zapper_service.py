import requests
import logging
from typing import List
from datetime import datetime
from app.config import ZAPPER_API_KEY
from app.schemas.financial import (
    PortfolioV2, TokenBalance, AppBalances, MetaTypeBalance, 
    NFTAsset, Transaction
)

logger = logging.getLogger(__name__)

ZAPPER_REST_URL = "https://api.zapper.xyz/v2"
ZAPPER_GRAPHQL_URL = "https://public.zapper.xyz/graphql"

class ZapperService:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {ZAPPER_API_KEY}",
            "Accept": "application/json"
        }
        self.graphql_headers = {
            "Content-Type": "application/json",
            "x-zapper-api-key": ZAPPER_API_KEY
        }

    def get_token_balances(self, wallet_address: str) -> PortfolioV2:
        query = """
            query PortfolioV2($addresses: [Address!]!, $networks: [Network!]) {
                portfolioV2(addresses: $addresses, networks: $networks) {
                    tokenBalances {
                        totalBalanceUSD
                        byToken {
                            edges {
                                node {
                                    symbol
                                    tokenAddress
                                    balance
                                    balanceUSD
                                    price
                                    imgUrlV2
                                    name
                                    network {
                                        name
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """
        try:
            response = requests.post(
                ZAPPER_GRAPHQL_URL,
                headers=self.graphql_headers,
                json={
                    "query": query,
                    "variables": {
                        "addresses": [wallet_address]
                    }
                })
            response.raise_for_status()
            result = response.json()

            if 'errors' in result:
                logger.warning(f"Zapper API errors: {result['errors']}")
                return PortfolioV2(total_balance_usd=0, tokens=[])

            portfolio_data = result.get('data', {}).get('portfolioV2', {})
            token_balances = portfolio_data.get('tokenBalances', {})
            
            if not token_balances:
                return PortfolioV2(total_balance_usd=0, tokens=[])

            tokens = []
            token_edges = token_balances.get('byToken', {}).get('edges', [])
            for edge in token_edges:
                node = edge.get('node', {})
                tokens.append(TokenBalance(
                    symbol=node.get('symbol', ''),
                    token_address=node.get('tokenAddress', ''),
                    balance=float(node.get('balance', 0)),
                    balance_usd=node.get('balanceUSD', 0),
                    price=node.get('price', 0),
                    img_url=node.get('imgUrlV2', ''),
                    name=node.get('name', ''),
                    network=node.get('network', {}).get('name', '') if node.get('network') else ''
                ))
            
            return PortfolioV2(
                total_balance_usd=token_balances.get('totalBalanceUSD', 0),
                tokens=tokens
            )
        except Exception as e:
            logger.error(f"Error fetching token balances: {str(e)}")
            return PortfolioV2(total_balance_usd=0, tokens=[])

    def get_app_balances(self, wallet_address: str) -> AppBalances:
        query = """
            query BreakdownByType($addresses: [Address!]!) {
                portfolioV2(addresses: $addresses) {
                    appBalances {
                        byMetaType {
                            totalCount
                            edges {
                                node {
                                    metaType
                                    positionCount
                                    balanceUSD
                                }
                            }
                        }
                    }
                }
            }
        """
        try:
            response = requests.post(
                ZAPPER_GRAPHQL_URL,
                headers=self.graphql_headers,
                json={
                    "query": query,
                    "variables": {
                        "addresses": [wallet_address]
                    }
                }
            )
            response.raise_for_status()
            result = response.json()

            if 'errors' in result:
                logger.warning(f"Zapper API errors: {result['errors']}")
                return AppBalances(by_meta_type=[])

            portfolio_data = result.get('data', {}).get('portfolioV2', {})
            app_balances = portfolio_data.get('appBalances', {})
            by_meta_type = app_balances.get('byMetaType', {})
            
            meta_types = []
            edges = by_meta_type.get('edges', [])
            for edge in edges:
                node = edge.get('node', {})
                meta_types.append(MetaTypeBalance(
                    meta_type=node.get('metaType', ''),
                    position_count=node.get('positionCount', 0),
                    balance_usd=node.get('balanceUSD', 0)
                ))

            return AppBalances(by_meta_type=meta_types)

        except Exception as e:
            logger.error(f"Error fetching app balances: {str(e)}")
            return AppBalances(by_meta_type=[])

    def get_nft_balances(self, wallet_address: str) -> List[NFTAsset]:
        query = """
        query NftCollectionWithNfts($collections: [NftCollectionInputV2!]!) {
        nftCollectionsV2(collections: $collections) {
            address
            nfts(first: 20) {
            edges {
                node {
                tokenId
                name
                mediasV3 {
                    images(first: 1) {
                    edges {
                        node {
                        original
                        }
                    }
                    }
                }
                estimatedValue {
                    valueUsd
                }
                }
            }
            }
        }
        }
        """
        
        try:
            response = requests.post(
                'https://public.zapper.xyz/graphql',
                headers={
                    'Content-Type': 'application/json',
                    'x-zapper-api-key': ZAPPER_API_KEY
                },
                json={
                    'query': query,
                    'variables': {
                        "collections": [
                            {
                                "address": "0xa449b4f43d9a33fcdcf397b9cc7aa909012709fd",
                                "chainId": 8453
                            }
                        ]
                    }
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'errors' in result:
                logger.warning(f"Zapper API errors: {result['errors']}")
                return []

            nfts = []
            collections = result.get('data', {}).get('nftCollectionsV2', [])
            for collection in collections:
                collection_address = collection.get('address', '')
                nft_data = collection.get('nfts', {})
                edges = nft_data.get('edges', [])
                
                for edge in edges:
                    node = edge.get('node', {})
                    images = node.get('mediasV3', {}).get('images', {}).get('edges', [])
                    img_url = images[0]['node']['original'] if images else None
                    
                    nfts.append(NFTAsset(
                        token_id=node.get('tokenId', ''),
                        name=node.get('name', ''),
                        collection_address=collection_address,
                        estimated_value=node.get('estimatedValue', {}).get('valueUsd'),
                        img_url=img_url,
                        network='base'
                    ))
            
            return nfts
        except Exception as e:
            logger.error(f"Error fetching NFT balances: {str(e)}")
            return []

    def get_transaction_history(self, wallet_address: str, limit: int = 20) -> List[Transaction]:
        query = """
            query TransactionHistoryV2($subjects: [Address!]!, $perspective: TransactionHistoryV2Perspective, $first: Int, $filters: TransactionHistoryV2FiltersArgs) {
                transactionHistoryV2(subjects: $subjects, perspective: $perspective, first: $first, filters: $filters) {
                    edges {
                        node {
                            ... on TimelineEventV2 {
                                methodSignature
                                methodSighash
                                transaction {
                                    blockNumber
                                    hash
                                    network
                                    timestamp
                                    fromUser {
                                        address
                                    }
                                    toUser {
                                        address
                                    }
                                }
                                interpretation {
                                    processedDescription
                                    description
                                    descriptionDisplayItems {
                                        ... on TokenDisplayItem {
                                            amountRaw
                                            tokenV2 {
                                                decimals
                                                priceData {
                                                    price
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """
        variables = {
            "subjects": [wallet_address],
            "perspective": "Signer",
            "first": limit,
            "filters": {"chainIds": [8453]}
        }
        
        try:
            response = requests.post(
                ZAPPER_GRAPHQL_URL,
                headers=self.graphql_headers,
                json={
                    "query": query,
                    "variables": variables
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if 'errors' in result:
                logger.warning(f"Zapper API errors: {result['errors']}")
                return []
            
            transactions = []
            tx_history = result.get('data', {}).get('transactionHistoryV2', {})
            edges = tx_history.get('edges', [])
            for edge in edges:
                node = edge.get('node', {})
                tx_data = node.get('transaction', {})
                interpretation = node.get('interpretation', {})
                
                # Convert timestamp from milliseconds to ISO format
                timestamp_ms = tx_data.get('timestamp')
                timestamp = datetime.utcfromtimestamp(timestamp_ms / 1000).isoformat() + 'Z' if timestamp_ms else None
                
                from_user = tx_data.get('fromUser', {})
                to_user = tx_data.get('toUser', {})
                
                # Calculate USD value from token display items
                value_usd = None
                display_items = interpretation.get('descriptionDisplayItems', [])
                for item in display_items:
                    if item.get('__typename') == 'TokenDisplayItem':
                        amount_raw = item.get('amountRaw')
                        token_v2 = item.get('tokenV2', {})
                        if amount_raw and token_v2:
                            decimals = token_v2.get('decimals', 18)
                            price_data = token_v2.get('priceData', {})
                            price = price_data.get('price')
                            if price:
                                try:
                                    # Calculate token value in USD
                                    amount = int(amount_raw) / (10 ** decimals)
                                    token_value_usd = amount * float(price)
                                    # Sum all token values for the transaction
                                    value_usd = (value_usd or 0) + token_value_usd
                                except (ValueError, TypeError) as e:
                                    logger.warning(f"Error calculating token value: {str(e)}")
                
                transactions.append(Transaction(
                    tx_hash=tx_data.get('hash', ''),
                    block_number=tx_data.get('blockNumber', 0),
                    timestamp=timestamp,
                    from_address=from_user.get('address', '') if from_user else '',
                    to_address=to_user.get('address', '') if to_user else '',
                    network=tx_data.get('network', ''),
                    method_signature=node.get('methodSignature'),
                    method_sighash=node.get('methodSighash'),
                    processed_description=interpretation.get('processedDescription'),
                    description=interpretation.get('description'),
                    value_usd=value_usd,
                    value_eth=None
                ))
            
            return transactions
        except Exception as e:
            logger.error(f"Error fetching transaction history: {str(e)}")
            return []