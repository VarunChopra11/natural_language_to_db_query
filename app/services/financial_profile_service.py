import logging
from app.services.zapper_service import ZapperService
from app.db.db import get_connection
from app.schemas.financial import FinancialProfile, PortfolioV2, AppBalances

logger = logging.getLogger(__name__)

class FinancialProfileService:
    def __init__(self):
        self.zapper = ZapperService()

    async def fetch_and_store_profile(self, wallet_address: str):
        try:
            # Fetch all data with safe defaults
            portfolio = self.zapper.get_token_balances(wallet_address) or PortfolioV2(total_balance_usd=0, tokens=[])
            app_balances = self.zapper.get_app_balances(wallet_address) or AppBalances(by_meta_type=[])
            nfts = self.zapper.get_nft_balances(wallet_address)
            transactions = self.zapper.get_transaction_history(wallet_address)
            
            profile = FinancialProfile(
                wallet_address=wallet_address,
                portfolio=portfolio,
                app_balances=app_balances,
                nft_assets=nfts,
                transactions=transactions
            )
            
            await self.store_profile(profile)
            
        except Exception as e:
            logger.error(f"Error fetching financial profile: {str(e)}")

    async def store_profile(self, profile: FinancialProfile):
        try:
            pool = await get_connection()
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # Get end_user_id and client_id
                    end_user = await conn.fetchrow(
                        "SELECT id, client_id FROM end_users WHERE wallet_address = $1",
                        profile.wallet_address
                    )
                    if not end_user:
                        logger.error(f"No end_user found for wallet: {profile.wallet_address}")
                        return
                    
                    end_user_id = end_user['id']
                    client_id = end_user['client_id']
                    
                    # Store portfolio
                    await conn.execute(
                        """INSERT INTO financial_portfolios 
                        (end_user_id, client_id, total_balance_usd, updated_at)
                        VALUES ($1, $2, $3, NOW())
                        ON CONFLICT (end_user_id) DO UPDATE
                        SET total_balance_usd = EXCLUDED.total_balance_usd,
                            updated_at = NOW()""",
                        end_user_id, client_id, profile.portfolio.total_balance_usd
                    )
                    
                    # Store token balances
                    for token in profile.portfolio.tokens:
                        await conn.execute(
                            """INSERT INTO token_balances 
                            (end_user_id, client_id, symbol, token_address, balance, balance_usd, 
                                price, network, img_url, updated_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                            ON CONFLICT (end_user_id, token_address) DO UPDATE
                            SET balance = EXCLUDED.balance, 
                                balance_usd = EXCLUDED.balance_usd,
                                price = EXCLUDED.price,
                                img_url = EXCLUDED.img_url,
                                updated_at = NOW()""",
                            end_user_id, client_id, token.symbol, token.token_address,
                            token.balance, token.balance_usd, token.price, 
                            token.network, token.img_url
                        )
                    
                    # Store app balances
                    for meta in profile.app_balances.by_meta_type:
                        await conn.execute(
                            """INSERT INTO app_balances 
                            (end_user_id, client_id, meta_type, position_count, balance_usd, updated_at)
                            VALUES ($1, $2, $3, $4, $5, NOW())
                            ON CONFLICT (end_user_id, meta_type) DO UPDATE
                            SET position_count = EXCLUDED.position_count, 
                                balance_usd = EXCLUDED.balance_usd,
                                updated_at = NOW()""",
                            end_user_id, client_id, meta.meta_type, 
                            meta.position_count, meta.balance_usd
                        )
                    
                    # Store NFTs
                    for nft in profile.nft_assets:
                        await conn.execute(
                            """INSERT INTO nft_assets 
                            (end_user_id, client_id, token_id, collection_address, name, 
                                estimated_value, img_url, network, last_updated)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                            ON CONFLICT (end_user_id, token_id, collection_address) DO UPDATE
                            SET name = EXCLUDED.name, 
                                estimated_value = EXCLUDED.estimated_value,
                                img_url = EXCLUDED.img_url,
                                network = EXCLUDED.network,
                                last_updated = NOW()""",
                            end_user_id, client_id, nft.token_id, 
                            nft.collection_address, nft.name, nft.estimated_value,
                            nft.img_url, nft.network
                        )
                    
                    # Store transactions
                    for tx in profile.transactions:
                        await conn.execute(
                            """INSERT INTO transaction_history 
                            (end_user_id, client_id, tx_hash, block_number, timestamp, from_address, 
                                to_address, network, method_signature, method_sighash, 
                                processed_description, description, value_usd, value_eth)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                            ON CONFLICT (tx_hash) DO UPDATE
                            SET block_number = EXCLUDED.block_number,
                                timestamp = EXCLUDED.timestamp,
                                from_address = EXCLUDED.from_address,
                                to_address = EXCLUDED.to_address,
                                method_signature = EXCLUDED.method_signature,
                                method_sighash = EXCLUDED.method_sighash,
                                processed_description = EXCLUDED.processed_description,
                                description = EXCLUDED.description,
                                value_usd = EXCLUDED.value_usd,
                                value_eth = EXCLUDED.value_eth""",
                            end_user_id, client_id, tx.tx_hash, tx.block_number, tx.timestamp,
                            tx.from_address, tx.to_address, tx.network, tx.method_signature,
                            tx.method_sighash, tx.processed_description, tx.description,
                            tx.value_usd, tx.value_eth
                        )
        except Exception as e:
            logger.error(f"Error storing financial profile: {str(e)}")