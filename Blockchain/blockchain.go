package blockchain

import "time"

//ブロックチェーンの構造体
type Blockchain struct {
	Chain []Block             //ブロックチェーン
	UncomfirmedChain []Block  //未認証チェーン
}

//最初のgenesis blockを生成
func (c *Blockchain) Creategenesisblock() error {
	var err error
	genesis := &Block{
		index:       0,
		timestamp:   time.Time{},
		transaction: []Transaction{},
		prevHash:    "",
		nonce:       0,
	}
	genesis.prevHash, err = genesis.CreateHash()
	if err != nil {
		return err
	}
	c.Chain = append(c.Chain, *genesis)
	return nil
}