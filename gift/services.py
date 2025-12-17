from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from typing import Optional, Dict, Any
from .models import GiftCard, GiftCardTransaction, GiftCardStatusType, GiftCardTransactionType
from payment.models import Payment, PaymentStatusType
from main.utils import money_quantize

class GiftCardService:
    """Service for managing gift card operations"""
    
    def create_gift_card(
        self,
        business_id: int,
        initial_amount: Decimal,
        currency: str = 'USD',
        purchaser_id: Optional[int] = None,
        recipient_name: Optional[str] = None,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        expires_at: Optional[timezone.datetime] = None,
        message: Optional[str] = None,
        notes: Optional[str] = None,
        payment_id: Optional[int] = None,
    ) -> GiftCard:
        """Create a new gift card"""
        with transaction.atomic():
            gift_card = GiftCard.objects.create(
                business_id=business_id,
                purchaser_id=purchaser_id,
                recipient_name=recipient_name,
                recipient_email=recipient_email,
                recipient_phone=recipient_phone,
                initial_amount=initial_amount,
                current_balance=initial_amount,
                currency=currency,
                expires_at=expires_at,
                message=message,
                notes=notes,
                payment_id=payment_id,
            )
            
            # Create purchase transaction
            GiftCardTransaction.objects.create(
                gift_card=gift_card,
                transaction_type=GiftCardTransactionType.PURCHASE,
                amount=initial_amount,
                balance_before=Decimal('0.00'),
                balance_after=initial_amount,
                payment_id=payment_id,
                description=f"Gift card purchased for ${initial_amount}"
            )
            
            return gift_card
    
    def redeem_gift_card(
        self,
        card_code: str,
        amount: Decimal,
        payment_id: Optional[int] = None,
        appointment_id: Optional[int] = None,
        description: Optional[str] = None,
        created_by_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Redeem an amount from a gift card"""
        with transaction.atomic():
            try:
                gift_card = GiftCard.objects.select_for_update().get(card_code=card_code)
            except GiftCard.DoesNotExist:
                raise ValueError("Gift card not found")
            
            if not gift_card.is_active:
                if gift_card.is_expired:
                    raise ValueError("Gift card has expired")
                elif gift_card.status == GiftCardStatusType.REDEEMED:
                    raise ValueError("Gift card has been fully redeemed")
                else:
                    raise ValueError("Gift card is not active")
            print("amount:: ", Decimal(amount))
            print("gift_card.current_balance:: ", gift_card.current_balance)
            amount = money_quantize(amount)
            current_balance = money_quantize(gift_card.current_balance)
            if amount > current_balance:
                raise ValueError(
                    f"Insufficient balance. Available: ${current_balance}, "
                    f"Requested: ${amount}"
                )
            
            balance_before = gift_card.current_balance
            gift_card.current_balance -= amount
            
            if gift_card.current_balance <= 0:
                gift_card.status = GiftCardStatusType.REDEEMED
                gift_card.redeemed_at = timezone.now()
                
            print("gift_card.current_balance:: ", gift_card.__dict__)
            
            gift_card.save()
            
            # Create redemption transaction
            transaction_obj = GiftCardTransaction.objects.create(
                gift_card=gift_card,
                transaction_type=GiftCardTransactionType.REDEMPTION,
                amount=amount,
                balance_before=balance_before,
                balance_after=current_balance,
                payment_id=payment_id,
                appointment_id=appointment_id,
                description=description or f"Redeemed ${amount} from gift card",
                created_by_id=created_by_id,
            )
            
            return {
                'gift_card': gift_card,
                'transaction': transaction_obj,
                'remaining_balance': gift_card.current_balance,
            }
    
    def validate_gift_card(self, card_code: str) -> GiftCard:
        """Validate a gift card code"""
        try:
            gift_card = GiftCard.objects.get(card_code=card_code)
        except GiftCard.DoesNotExist:
            raise ValueError("Gift card not found")
        
        if not gift_card.is_active:
            if gift_card.is_expired:
                raise ValueError("Gift card has expired")
            elif gift_card.status == GiftCardStatusType.REDEEMED:
                raise ValueError("Gift card has been fully redeemed")
            else:
                raise ValueError("Gift card is not active")
        
        return gift_card
    
    def refund_gift_card(
        self,
        gift_card_id: int,
        amount: Decimal,
        refund_payment_id: Optional[int] = None,
        description: Optional[str] = None,
        created_by_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Refund an amount to a gift card"""
        with transaction.atomic():
            try:
                gift_card = GiftCard.objects.select_for_update().get(id=gift_card_id)
            except GiftCard.DoesNotExist:
                raise ValueError("Gift card not found")
            
            if gift_card.status == GiftCardStatusType.CANCELLED:
                raise ValueError("Cannot refund to a cancelled gift card")
            
            # Reactivate if needed
            if gift_card.status == GiftCardStatusType.REDEEMED:
                gift_card.status = GiftCardStatusType.ACTIVE
                gift_card.redeemed_at = None
            
            balance_before = gift_card.current_balance
            gift_card.current_balance += amount
            
            # Ensure balance doesn't exceed initial amount (unless business allows it)
            if gift_card.current_balance > gift_card.initial_amount:
                gift_card.initial_amount = gift_card.current_balance
            
            gift_card.save()
            
            # Create refund transaction
            transaction_obj = GiftCardTransaction.objects.create(
                gift_card=gift_card,
                transaction_type=GiftCardTransactionType.REFUND,
                amount=amount,
                balance_before=balance_before,
                balance_after=gift_card.current_balance,
                payment_id=refund_payment_id,
                description=description or f"Refunded ${amount} to gift card",
                created_by_id=created_by_id,
            )
            
            return {
                'gift_card': gift_card,
                'transaction': transaction_obj,
                'new_balance': gift_card.current_balance,
            }
    
    def cancel_gift_card(
        self,
        gift_card_id: int,
        reason: Optional[str] = None,
        created_by_id: Optional[int] = None,
    ) -> GiftCard:
        """Cancel a gift card"""
        with transaction.atomic():
            try:
                gift_card = GiftCard.objects.select_for_update().get(id=gift_card_id)
            except GiftCard.DoesNotExist:
                raise ValueError("Gift card not found")
            
            if gift_card.status == GiftCardStatusType.CANCELLED:
                raise ValueError("Gift card is already cancelled")
            
            gift_card.status = GiftCardStatusType.CANCELLED
            gift_card.save()
            
            # Create cancellation transaction
            GiftCardTransaction.objects.create(
                gift_card=gift_card,
                transaction_type=GiftCardTransactionType.ADJUSTMENT,
                amount=Decimal('0.00'),
                balance_before=gift_card.current_balance,
                balance_after=gift_card.current_balance,
                description=f"Gift card cancelled. Reason: {reason or 'No reason provided'}",
                created_by_id=created_by_id,
            )
            
            return gift_card
    
    def adjust_gift_card_balance(
        self,
        gift_card_id: int,
        adjustment_amount: Decimal,
        description: Optional[str] = None,
        created_by_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Adjust gift card balance (for admin adjustments)"""
        with transaction.atomic():
            try:
                gift_card = GiftCard.objects.select_for_update().get(id=gift_card_id)
            except GiftCard.DoesNotExist:
                raise ValueError("Gift card not found")
            
            if gift_card.status == GiftCardStatusType.CANCELLED:
                raise ValueError("Cannot adjust a cancelled gift card")
            
            balance_before = gift_card.current_balance
            gift_card.current_balance += adjustment_amount
            
            if gift_card.current_balance < 0:
                raise ValueError("Balance cannot be negative")
            
            # Reactivate if needed
            if gift_card.status == GiftCardStatusType.REDEEMED and gift_card.current_balance > 0:
                gift_card.status = GiftCardStatusType.ACTIVE
                gift_card.redeemed_at = None
            
            gift_card.save()
            
            # Create adjustment transaction
            transaction_obj = GiftCardTransaction.objects.create(
                gift_card=gift_card,
                transaction_type=GiftCardTransactionType.ADJUSTMENT,
                amount=abs(adjustment_amount),
                balance_before=balance_before,
                balance_after=gift_card.current_balance,
                description=description or f"Balance adjusted by ${adjustment_amount}",
                created_by_id=created_by_id,
            )
            
            return {
                'gift_card': gift_card,
                'transaction': transaction_obj,
                'new_balance': gift_card.current_balance,
            }

